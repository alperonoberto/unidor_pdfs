def versions_match(first: str, second: str) -> bool:
    # Return whether two release tags represent the same version.
    normalized_first = first.strip().casefold().removeprefix("v")
    normalized_second = second.strip().casefold().removeprefix("v")
    return normalized_first == normalized_second


def is_newer_version(candidate: str, current: str) -> bool:
    candidate_parts = _numeric_version_parts(candidate)
    current_parts = _numeric_version_parts(current)
    width = max(len(candidate_parts), len(current_parts))
    return candidate_parts + (0,) * (width - len(candidate_parts)) > (
        current_parts + (0,) * (width - len(current_parts))
    )


def _numeric_version_parts(version: str) -> tuple[int, ...]:
    normalized = version.strip().casefold().removeprefix("v")
    parts = normalized.split(".")
    if not parts or any(not part.isdecimal() for part in parts):
        raise ValueError(f"Formato de versión no compatible: {version}")
    return tuple(int(part) for part in parts)
