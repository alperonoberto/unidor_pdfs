import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from unidor_pdfs.update_manager import (
    ReleaseAsset,
    UpdateError,
    download_update,
    install_update,
    latest_release,
    select_release_asset,
)


class ReleaseAssetTests(unittest.TestCase):
    def make_release(self, name, url=None):
        return {
            "assets": [
                {
                    "name": name,
                    "browser_download_url": url or (
                        "https://github.com/alperonoberto/unidor_pdfs/"
                        "releases/download/v1.0.9/" + name
                    ),
                    "size": 1234,
                    "digest": "sha256:" + "a" * 64,
                }
            ]
        }

    def test_selects_windows_amd64_asset(self):
        asset = select_release_asset(
            self.make_release("unir_pdfs-windows-amd64.exe"),
            system="Windows",
            machine="AMD64",
        )
        self.assertEqual(asset.name, "unir_pdfs-windows-amd64.exe")

    def test_selects_linux_x86_64_asset(self):
        asset = select_release_asset(
            self.make_release("unir_pdfs-linux-amd64"),
            system="Linux",
            machine="x86_64",
        )
        self.assertEqual(asset.name, "unir_pdfs-linux-amd64")

    def test_rejects_unsupported_system_and_architecture(self):
        with self.assertRaises(UpdateError):
            select_release_asset({}, system="Darwin", machine="x86_64")
        with self.assertRaises(UpdateError):
            select_release_asset({}, system="Linux", machine="aarch64")

    def test_rejects_missing_platform_asset(self):
        with self.assertRaises(UpdateError):
            select_release_asset({}, system="Linux", machine="x86_64")

    def test_rejects_asset_url_outside_github_release(self):
        release = self.make_release(
            "unir_pdfs-linux-amd64",
            url="https://example.com/unir_pdfs-linux-amd64",
        )
        with self.assertRaises(UpdateError):
            select_release_asset(release, system="Linux", machine="x86_64")

    def test_rejects_unsupported_integrity_digest(self):
        release = self.make_release("unir_pdfs-linux-amd64")
        release["assets"][0]["digest"] = "md5:" + "a" * 32
        with self.assertRaises(UpdateError):
            select_release_asset(release, system="Linux", machine="x86_64")


class LatestReleaseTests(unittest.TestCase):
    def test_selects_latest_official_release_and_ignores_prereleases(self):
        releases = [
            {"tag_name": "v1.0.9-beta", "assets": [], "prerelease": False},
            {"tag_name": "v1.0.8", "assets": [], "prerelease": False},
            {"tag_name": "v1.0.10-rc.1", "assets": [], "prerelease": True},
            {"tag_name": "v9.0.0", "assets": [], "draft": True},
            {"tag_name": "v1.0.9", "assets": [], "prerelease": False},
        ]
        response = io.BytesIO(json.dumps(releases).encode("utf-8"))
        with patch("unidor_pdfs.update_manager.urllib.request.urlopen", return_value=response):
            release = latest_release()

        self.assertEqual(release["tag_name"], "v1.0.9")

    def test_raises_when_no_official_release_is_available(self):
        releases = [
            {"tag_name": "v1.0.9-beta", "assets": [], "prerelease": True},
            {"tag_name": "v1.0.10", "assets": [], "draft": True},
        ]
        response = io.BytesIO(json.dumps(releases).encode("utf-8"))
        with (
            patch("unidor_pdfs.update_manager.urllib.request.urlopen", return_value=response),
            self.assertRaises(ValueError),
        ):
            latest_release()


class DownloadUpdateTests(unittest.TestCase):
    def test_downloads_and_verifies_linux_executable(self):
        contents = b"\x7fELFtest"
        asset = ReleaseAsset(
            name="unir_pdfs-linux-amd64",
            url="https://github.com/alperonoberto/unidor_pdfs/releases/download/v1/test",
            size=len(contents),
            digest="sha256:" + hashlib.sha256(contents).hexdigest(),
        )
        with tempfile.TemporaryDirectory() as directory:
            executable_path = Path(directory) / "unir_pdfs"
            executable_path.write_bytes(b"old executable")
            executable_path.chmod(0o755)
            progress = []
            with (
                patch.object(sys, "frozen", True, create=True),
                patch("unidor_pdfs.update_manager.platform.system", return_value="Linux"),
                patch(
                    "unidor_pdfs.update_manager.urllib.request.urlopen",
                    return_value=io.BytesIO(contents),
                ),
            ):
                staged_path = download_update(
                    asset,
                    executable_path,
                    progress_callback=lambda downloaded, total: progress.append(
                        (downloaded, total)
                    ),
                )

            self.assertEqual(staged_path.read_bytes(), contents)
            self.assertTrue(staged_path.stat().st_mode & 0o100)
            self.assertEqual(
                progress,
                [(0, len(contents)), (len(contents), len(contents))],
            )
            staged_path.unlink()

    def test_rejects_bad_digest_and_removes_partial_download(self):
        contents = b"\x7fELFtest"
        asset = ReleaseAsset(
            name="unir_pdfs-linux-amd64",
            url="https://github.com/alperonoberto/unidor_pdfs/releases/download/v1/test",
            size=len(contents),
            digest="sha256:" + "0" * 64,
        )
        with tempfile.TemporaryDirectory() as directory:
            executable_path = Path(directory) / "unir_pdfs"
            executable_path.write_bytes(b"old executable")
            with (
                patch.object(sys, "frozen", True, create=True),
                patch("unidor_pdfs.update_manager.platform.system", return_value="Linux"),
                patch(
                    "unidor_pdfs.update_manager.urllib.request.urlopen",
                    return_value=io.BytesIO(contents),
                ),
            ):
                with self.assertRaises(UpdateError):
                    download_update(asset, executable_path)

            self.assertEqual(list(Path(directory).glob("*.update")), [])
            self.assertEqual(executable_path.read_bytes(), b"old executable")

    def test_rejects_download_that_is_not_an_executable(self):
        contents = b"not an executable"
        asset = ReleaseAsset(
            name="unir_pdfs-linux-amd64",
            url="https://github.com/alperonoberto/unidor_pdfs/releases/download/v1/test",
            size=len(contents),
            digest="sha256:" + hashlib.sha256(contents).hexdigest(),
        )
        with tempfile.TemporaryDirectory() as directory:
            executable_path = Path(directory) / "unir_pdfs"
            executable_path.write_bytes(b"old executable")
            with (
                patch.object(sys, "frozen", True, create=True),
                patch("unidor_pdfs.update_manager.platform.system", return_value="Linux"),
                patch(
                    "unidor_pdfs.update_manager.urllib.request.urlopen",
                    return_value=io.BytesIO(contents),
                ),
            ):
                with self.assertRaises(UpdateError):
                    download_update(asset, executable_path)

            self.assertEqual(executable_path.read_bytes(), b"old executable")
            self.assertEqual(list(Path(directory).glob("*.update")), [])


class InstallUpdateTests(unittest.TestCase):
    def test_windows_helper_uses_backup_path_when_replacing_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            executable_path = Path(directory) / "unir_pdfs.exe"
            executable_path.write_bytes(b"old executable")
            staged_path = Path(directory) / "staged.exe"
            staged_path.write_bytes(b"new executable")
            with (
                patch("unidor_pdfs.update_manager.platform.system", return_value="Windows"),
                patch("unidor_pdfs.update_manager.shutil.which", return_value="powershell.exe"),
                patch("unidor_pdfs.update_manager.subprocess.Popen") as popen,
            ):
                install_update(staged_path, executable_path, 123)

            command = popen.call_args.args[0]
            script_path = Path(command[8])
            try:
                script = script_path.read_text(encoding="utf-8")
                self.assertIn(
                    "[System.IO.File]::Replace($StagedPath, $TargetPath, $BackupPath)",
                    script,
                )
                self.assertIn(
                    "$env:PYINSTALLER_RESET_ENVIRONMENT = '1'",
                    script,
                )
                self.assertEqual(
                    command[9:12],
                    ["123", str(staged_path), str(executable_path)],
                )
                backup_path = Path(command[12])
                self.assertEqual(backup_path.parent, executable_path.parent)
                self.assertEqual(backup_path.suffix, ".backup")
            finally:
                script_path.unlink(missing_ok=True)

    def test_restarts_from_replaced_linux_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            executable_path = Path(directory) / "unir_pdfs"
            executable_path.write_bytes(b"old executable")
            staged_path = Path(directory) / "staged"
            staged_path.write_bytes(b"new executable")
            with (
                patch("unidor_pdfs.update_manager.platform.system", return_value="Linux"),
                patch.dict(os.environ, {"UNIDOR_TEST_ENV": "preserved"}),
                patch("unidor_pdfs.update_manager.subprocess.Popen") as popen,
            ):
                install_update(staged_path, executable_path, 123)

            self.assertEqual(executable_path.read_bytes(), b"new executable")
            popen.assert_called_once()
            child_environment = popen.call_args.kwargs["env"]
            self.assertEqual(child_environment["PYINSTALLER_RESET_ENVIRONMENT"], "1")
            self.assertEqual(child_environment["UNIDOR_TEST_ENV"], "preserved")
            self.assertEqual(list(Path(directory).glob("*.backup")), [])

    def test_rolls_back_if_linux_restart_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            executable_path = Path(directory) / "unir_pdfs"
            executable_path.write_bytes(b"old executable")
            staged_path = Path(directory) / "staged"
            staged_path.write_bytes(b"new executable")
            with (
                patch("unidor_pdfs.update_manager.platform.system", return_value="Linux"),
                patch("unidor_pdfs.update_manager.subprocess.Popen", side_effect=OSError("failed")),
            ):
                with self.assertRaises(OSError):
                    install_update(staged_path, executable_path, 123)

            self.assertEqual(executable_path.read_bytes(), b"old executable")
            self.assertEqual(list(Path(directory).glob("*.backup")), [])


if __name__ == "__main__":
    unittest.main()
