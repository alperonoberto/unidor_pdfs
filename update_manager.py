import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from version_utils import is_newer_version, is_stable_version


GITHUB_REPO = "alperonoberto/unidor_pdfs"
MAX_UPDATE_SIZE = 512 * 1024 * 1024
USER_AGENT = "UnidorPDFs-Updater"


class UpdateError(Exception):
    pass


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    url: str
    size: int
    digest: str | None


def latest_release() -> dict[str, Any]:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases?per_page=100"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=10) as response:
        releases = json.loads(response.read().decode("utf-8"))
    if not isinstance(releases, list):
        raise ValueError("La respuesta de GitHub no contiene una lista de versiones.")

    latest = None
    for release in releases:
        if (
            not isinstance(release, dict)
            or release.get("draft")
            or release.get("prerelease")
            or not isinstance(release.get("tag_name"), str)
            or not is_stable_version(release["tag_name"])
            or not isinstance(release.get("assets"), list)
        ):
            continue
        if latest is None or is_newer_version(
            release["tag_name"], latest["tag_name"]
        ):
            latest = release

    if latest is None:
        raise ValueError("GitHub no contiene ninguna versión oficial disponible.")
    return latest


def select_release_asset(
    release: dict[str, Any],
    system: str | None = None,
    machine: str | None = None,
) -> ReleaseAsset:
    system_name = (system or platform.system()).casefold()
    architecture = (machine or platform.machine()).casefold()
    if system_name not in {"windows", "linux"}:
        raise UpdateError("Las actualizaciones automáticas no están disponibles para este sistema.")
    if architecture not in {"amd64", "x86_64", "x64"}:
        raise UpdateError("Las actualizaciones automáticas solo están disponibles para x86-64.")

    if system_name == "windows":
        expected_name = "unir_pdfs-windows-amd64.exe"
    else:
        expected_name = "unir_pdfs-linux-amd64"

    for asset in release.get("assets", []):
        if asset.get("name") != expected_name:
            continue
        url = asset.get("browser_download_url", "")
        parsed_url = urllib.parse.urlparse(url)
        if (
            parsed_url.scheme != "https"
            or parsed_url.hostname != "github.com"
            or not parsed_url.path.startswith(
                f"/{GITHUB_REPO}/releases/download/"
            )
        ):
            raise UpdateError("La URL del archivo de actualización no es válida.")
        size = asset.get("size")
        if (
            not isinstance(size, int)
            or isinstance(size, bool)
            or size <= 0
            or size > MAX_UPDATE_SIZE
        ):
            raise UpdateError("El tamaño del archivo de actualización no es válido.")
        digest = asset.get("digest")
        if isinstance(digest, str) and not digest.startswith("sha256:"):
            raise UpdateError("El formato de verificación de la release no es compatible.")
        return ReleaseAsset(
            name=expected_name,
            url=url,
            size=size,
            digest=digest if isinstance(digest, str) else None,
        )

    raise UpdateError(
        f"La release no incluye el ejecutable necesario ({expected_name})."
    )


def download_update(asset: ReleaseAsset, executable_path: Path) -> Path:
    executable_path = executable_path.resolve()
    if not getattr(sys, "frozen", False):
        raise UpdateError("La instalación automática solo está disponible en el ejecutable.")

    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{executable_path.name}.",
            suffix=".update",
            dir=executable_path.parent,
        )
    except OSError as error:
        raise UpdateError(
            "No hay permisos para instalar una actualización en la carpeta de la aplicación."
        ) from error

    temporary_path = Path(temporary_name)
    digest = hashlib.sha256()
    downloaded = 0
    try:
        request = urllib.request.Request(
            asset.url,
            headers={"User-Agent": USER_AGENT},
        )
        with os.fdopen(descriptor, "wb") as output:
            with urllib.request.urlopen(request, timeout=30) as response:
                while chunk := response.read(1024 * 1024):
                    downloaded += len(chunk)
                    if downloaded > MAX_UPDATE_SIZE:
                        raise UpdateError("El archivo descargado supera el tamaño permitido.")
                    digest.update(chunk)
                    output.write(chunk)

        if downloaded != asset.size:
            raise UpdateError("El tamaño del archivo descargado no coincide con la release.")
        if asset.digest:
            algorithm, separator, expected_digest = asset.digest.partition(":")
            if algorithm != "sha256" or not separator:
                raise UpdateError("El formato de verificación de la release no es compatible.")
            if digest.hexdigest().casefold() != expected_digest.casefold():
                raise UpdateError("La verificación de integridad de la actualización falló.")

        expected_magic = b"MZ" if platform.system() == "Windows" else b"\x7fELF"
        with temporary_path.open("rb") as downloaded_file:
            if downloaded_file.read(len(expected_magic)) != expected_magic:
                raise UpdateError("El archivo descargado no parece ser un ejecutable válido.")

        if platform.system() == "Linux":
            current_mode = stat.S_IMODE(executable_path.stat().st_mode)
            temporary_path.chmod(current_mode | stat.S_IXUSR)
        return temporary_path
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def install_update(
    staged_path: Path,
    executable_path: Path,
    parent_pid: int,
) -> None:
    if platform.system() == "Windows":
        _start_windows_update_helper(staged_path, executable_path, parent_pid)
        return
    if platform.system() != "Linux":
        raise UpdateError("Las actualizaciones automáticas no están disponibles para este sistema.")

    backup_path = _create_backup(executable_path)
    try:
        os.replace(staged_path, executable_path)
        subprocess.Popen([str(executable_path)], cwd=executable_path.parent)
    except Exception:
        if backup_path.exists():
            os.replace(backup_path, executable_path)
        raise
    backup_path.unlink(missing_ok=True)


def _create_backup(executable_path: Path) -> Path:
    descriptor, backup_name = tempfile.mkstemp(
        prefix=f".{executable_path.name}.",
        suffix=".backup",
        dir=executable_path.parent,
    )
    os.close(descriptor)
    backup_path = Path(backup_name)
    backup_path.unlink()
    try:
        shutil.copy2(executable_path, backup_path)
    except Exception:
        backup_path.unlink(missing_ok=True)
        raise
    return backup_path


def _start_windows_update_helper(
    staged_path: Path,
    executable_path: Path,
    parent_pid: int,
) -> None:
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if powershell is None:
        raise UpdateError("No se encontró PowerShell para completar la instalación.")

    backup_descriptor, backup_name = tempfile.mkstemp(
        prefix=f".{executable_path.name}.",
        suffix=".backup",
        dir=executable_path.parent,
    )
    os.close(backup_descriptor)
    backup_path = Path(backup_name)
    backup_path.unlink()
    script = r"""
param([int]$ParentPid, [string]$StagedPath, [string]$TargetPath, [string]$BackupPath)
$ErrorActionPreference = 'Stop'
try {
    Wait-Process -Id $ParentPid -ErrorAction SilentlyContinue
    [System.IO.File]::Replace($StagedPath, $TargetPath, $BackupPath)
    Start-Process -FilePath $TargetPath -WorkingDirectory (Split-Path $TargetPath)
    Remove-Item -LiteralPath $BackupPath -Force
} catch {
    if (Test-Path -LiteralPath $BackupPath) {
        try {
            if (Test-Path -LiteralPath $TargetPath) {
                Move-Item -LiteralPath $BackupPath -Destination $TargetPath -Force
            } else {
                Move-Item -LiteralPath $BackupPath -Destination $TargetPath
            }
        } catch {}
    }
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show(
        "The update could not be installed: $($_.Exception.Message)",
        "Unidor PDFs update",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    )
} finally {
    Remove-Item -LiteralPath $StagedPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $BackupPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
}
"""
    script_descriptor, script_name = tempfile.mkstemp(
        prefix="unidor-update-",
        suffix=".ps1",
    )
    script_path = Path(script_name)
    try:
        with os.fdopen(script_descriptor, "w", encoding="utf-8") as script_file:
            script_file.write(script)
        subprocess.Popen(
            [
                powershell,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-WindowStyle",
                "Hidden",
                "-File",
                str(script_path),
                str(parent_pid),
                str(staged_path),
                str(executable_path),
                str(backup_path),
            ],
            close_fds=True,
        )
    except Exception:
        script_path.unlink(missing_ok=True)
        backup_path.unlink(missing_ok=True)
        raise
