import json
import os
import time
import re

# ==== File I/O Operations for JSONL files ====


def read_jsonl_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def write_jsonl_file(output_file, data):
    with open(output_file, "w", encoding="utf-8") as f:
        for entry in data:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")


def append_jsonl_entry(output_file, entry, file_lock):
    """Appends a single entry to a JSONL file in a thread-safe manner."""
    with file_lock:
        with open(output_file, "a", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")

# ==== Processing JSONL Input Files ====


def process_jsonl_input_files(file_paths, folder_paths, file_type=None):
    """Processes JSONL input files from given file paths and folder paths."""
    result_files = file_paths or []

    for results_folder in folder_paths or []:
        folder_files = list_jsonl_files(results_folder, startswith=file_type)
        result_files.extend(folder_files)

    if result_files == []:
        print("[Error] No JSONL files included for analysis.")
        exit(1)

    return result_files


def list_jsonl_files(folder_path, startswith=None):
    """Lists all JSONL results files in a given folder. (Must start with 'results' and end with '.jsonl')"""
    return [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if (startswith is None or f.startswith(startswith)) and f.endswith(".jsonl") and os.path.isfile(os.path.join(folder_path, f))
    ]

# ==== Tags ====


def validate_tag(tag):
    """
    Validates that a tag is safe to use in a filename.

    Args:
        tag (str): The tag to validate

    Returns:
        tuple: (is_valid, error_message)
            - is_valid (bool): True if tag is valid, False otherwise
            - error_message (str): Reason for validation failure or None if valid
    """
    if tag is None:
        return True, None

    # Check for empty string after stripping whitespace
    if len(tag.strip()) == 0:
        return False, "Tag cannot be empty or whitespace only"

    # Check length (reasonable max length for filename component)
    MAX_LENGTH = 50
    if len(tag) > MAX_LENGTH:
        return False, f"Tag exceeds maximum length of {MAX_LENGTH} characters"

    # Check for valid characters - alphanumeric, dash and underscore only
    pattern = re.compile(r"^[a-zA-Z0-9_-]+$")
    if not pattern.match(tag):
        return (
            False,
            "Tag can only contain letters, numbers, dash (-) and underscore (_)",
        )

    return True, None


def validate_and_get_tag(tag):
    if not tag:
        return None
    valid, err = validate_tag(tag)
    if not valid:
        print(f"Error: Invalid tag: {err}")
        exit(1)
    return tag
