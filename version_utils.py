def versions_match(first: str, second: str) -> bool:
    # Return whether two release tags represent the same version.
    normalized_first = first.strip().casefold().removeprefix("v")
    normalized_second = second.strip().casefold().removeprefix("v")
    return normalized_first == normalized_second
