
import hashlib
from src.generate_data import generate_all
from src.config import RAW_DIR


def calculate_file_hash(path):
    digest = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)

    return digest.hexdigest()


def test_generation_is_reproducible():
    generate_all()

    files = sorted(RAW_DIR.glob("*.csv"))

    first_hashes = {
        file.name: calculate_file_hash(file)
        for file in files
    }

    generate_all()

    second_hashes = {
        file.name: calculate_file_hash(file)
        for file in sorted(RAW_DIR.glob("*.csv"))
    }

    assert first_hashes == second_hashes
