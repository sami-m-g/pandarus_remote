"""Helper script to get the SHA256 hash of all files in the data directory."""

from pathlib import Path

from pandarus.utils.io import sha256_file

if __name__ == "__main__":
    # Iterate over all files in data directory
    data_dir = Path(__file__).parent.parent / "tests" / "data"
    for file_path in data_dir.iterdir():
        if file_path.is_file():
            print(f"{file_path.name}: {sha256_file(file_path)}")
