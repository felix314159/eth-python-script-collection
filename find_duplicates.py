import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileInfo:
    absolute_path: str
    relative_path: str
    name: str
    is_file: bool


def is_path_excluded(absolute_path, excluded_folders):
    """Check if path contains any excluded folder as a complete directory name."""
    path_parts = Path(absolute_path).parts
    return any(folder in path_parts for folder in excluded_folders)


def search_files_and_folders(basedir) -> list:
    all_items = []  # store FileInfo objects
    excluded_folders = {
        ".cache",
        ".git",
        ".github",
        ".meta",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        ".vscode",
        "logs",
        "fixtures",
        "site",
        "stubs",
    }

    excluded_file_extensions = {"pyc"}

    for dirpath, dirnames, filenames in os.walk(basedir):
        # handle files
        for f in filenames:  # filename is f
            # get absolute path to file
            relative_path = os.path.join(dirpath, f)
            absolute_path = os.path.abspath(relative_path)
            file_extension = Path(absolute_path).suffix[1:]

            if is_path_excluded(absolute_path, excluded_folders):
                continue

            if file_extension in excluded_file_extensions:
                continue

            all_items.append(
                FileInfo(
                    absolute_path=absolute_path, relative_path=relative_path, name=f, is_file=True
                )
            )

        # handle folders
        for d in dirnames:  # foldername is d
            if d == "__pycache__":
                continue

            relative_path = os.path.join(dirpath, d)
            absolute_path = os.path.abspath(relative_path)

            if is_path_excluded(absolute_path, excluded_folders):
                continue

            all_items.append(
                FileInfo(
                    absolute_path=absolute_path, relative_path=relative_path, name=d, is_file=False
                )
            )

    return all_items


def main():
    cwd = "."
    print("Scanning subfolders..")
    all_items = search_files_and_folders(cwd)
    assert len(all_items) > 0, f"Did not find any files or folders"

    # Use defaultdict to store lists of FileInfo objects
    folder_occurrences = defaultdict(list)
    file_occurrences = defaultdict(list)

    for fi in all_items:
        if fi.is_file:
            file_occurrences[fi.name].append(fi)
        else:  # isFolder
            folder_occurrences[fi.name].append(fi)

    print("\n--- File Occurrences (Sorted by count, descending) ---")
    # Sort file occurrences by the number of items in the list (their count)
    # The key for sorting is the length of the list associated with each name
    sorted_file_occurrences = sorted(
        file_occurrences.items(),
        key=lambda item: len(item[1]),  # item[1] is the list of FileInfo objects
        reverse=True,
    )

    for name, files in sorted_file_occurrences:
        count = len(files)
        if count == 1:
            continue
        print(f"Name: '{name}' - Occurrences: {count}")
        # if count > 1 and count < 50:
        #     print("  Duplicate paths:")
        #     for file_info in files:
        #         print(f"      Relative Path: {file_info.relative_path}")
        # print()

    print("\n--- Folder Occurrences (Sorted by count, descending) ---")
    # Sort folder occurrences similarly
    sorted_folder_occurrences = sorted(
        folder_occurrences.items(), key=lambda item: len(item[1]), reverse=True
    )

    for name, folders in sorted_folder_occurrences:
        count = len(folders)
        if count == 1:
            continue
        print(f"Name: '{name}' - Occurrences: {count}")
        # if count > 1 and count < 50:
        #     print("  Duplicate paths:")
        #     for folder_info in folders:
        #         print(f"      Relative Path: {folder_info.relative_path}")
        #     print()


main()
