from collections.abc import Iterable
import os
from pathlib import Path


def collect_pdf_files(
    existing_files: Iterable[str], candidate_paths: Iterable[str]
) -> tuple[list[str], int]:
    known_paths = {
        os.path.normcase(os.path.abspath(path)) for path in existing_files
    }
    new_files = []
    rejected_count = 0

    for candidate in candidate_paths:
        path = Path(candidate).expanduser()
        if path.suffix.casefold() != ".pdf" or not path.is_file():
            rejected_count += 1
            continue

        normalized_path = str(path.resolve())
        key = os.path.normcase(normalized_path)
        if key not in known_paths:
            known_paths.add(key)
            new_files.append(normalized_path)

    return new_files, rejected_count
