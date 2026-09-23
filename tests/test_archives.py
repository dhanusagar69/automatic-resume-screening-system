import zipfile

from resume_screening.archives import input_directory
from resume_screening.pipeline import screen_input


def test_zip_input_is_screened(tmp_path):
    archive_path = tmp_path / "resumes.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("nested/candidate.txt", "Asha Rao\nPython LangGraph RAG FastAPI")

    payload = screen_input(archive_path)

    assert payload["summary"]["total_resumes"] == 1
    assert payload["summary"]["eligible"] == 1


def test_zip_path_traversal_is_rejected(tmp_path):
    archive_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", "Python LangGraph")

    try:
        next(input_directory(archive_path))
    except ValueError as error:
        assert "Unsafe archive" in str(error)
    else:
        raise AssertionError("Unsafe ZIP path was accepted")
