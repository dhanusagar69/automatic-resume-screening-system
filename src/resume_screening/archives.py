import zipfile
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

SUPPORTED_INPUT_FILES = {".pdf", ".docx", ".txt", ".md"}


def safe_extract_zip(archive_path: Path, destination: Path) -> None:
    destination_root = destination.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            member_path = (destination / member.filename).resolve()
            if destination_root != member_path and destination_root not in member_path.parents:
                raise ValueError(f"Unsafe archive member path: {member.filename}")
        archive.extractall(destination)


def input_directory(input_path: Path):
    """Yield a directory for either a resume folder or a ZIP archive."""
    if input_path.is_dir():
        yield input_path
        return
    if input_path.is_file() and input_path.suffix.lower() == ".zip":
        with TemporaryDirectory(prefix="resume-screening-") as temporary_directory:
            extraction_directory = Path(temporary_directory)
            safe_extract_zip(input_path, extraction_directory)
            yield extraction_directory
        return
    if input_path.is_file() and input_path.suffix.lower() in SUPPORTED_INPUT_FILES:
        with TemporaryDirectory(prefix="resume-screening-") as temporary_directory:
            temporary_path = Path(temporary_directory) / input_path.name
            shutil.copy2(input_path, temporary_path)
            yield Path(temporary_directory)
        return
    raise ValueError(f"Input must be a directory, supported resume file, or .zip archive: {input_path}")
