def versions_match(first: str, second: str) -> bool:
    # Return whether two release tags represent the same version.
    normalized_first = first.strip().casefold().removeprefix("v")
    normalized_second = second.strip().casefold().removeprefix("v")
    return normalized_first == normalized_second


def is_newer_version(candidate: str, current: str) -> bool:
    candidate_parts, candidate_is_prerelease = _version_parts(candidate)
    current_parts, current_is_prerelease = _version_parts(current)
    width = max(len(candidate_parts), len(current_parts))
    normalized_candidate = candidate_parts + (0,) * (width - len(candidate_parts))
    normalized_current = current_parts + (0,) * (width - len(current_parts))
    if normalized_candidate != normalized_current:
        return normalized_candidate > normalized_current
    return current_is_prerelease and not candidate_is_prerelease


def is_stable_version(version: str) -> bool:
    try:
        _numeric_version_parts(version)
    except ValueError:
        return False
    return True


def _version_parts(version: str) -> tuple[tuple[int, ...], bool]:
    normalized = version.strip().casefold().removeprefix("v")
    numeric_version, separator, prerelease = normalized.partition("-")
    if separator and not prerelease:
        raise ValueError(f"Formato de versión no compatible: {version}")
    return _numeric_version_parts(numeric_version), bool(separator)


def _numeric_version_parts(version: str) -> tuple[int, ...]:
    normalized = version.strip().casefold().removeprefix("v")
    parts = normalized.split(".")
    if not parts or any(not part.isdecimal() for part in parts):
        raise ValueError(f"Formato de versión no compatible: {version}")
    return tuple(int(part) for part in parts)
