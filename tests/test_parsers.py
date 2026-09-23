from pathlib import Path

from resume_screening.parsers import parse_resume


def test_github_profile_without_protocol_is_extracted(tmp_path: Path):
    resume_path = tmp_path / "candidate.txt"
    resume_path.write_text("Asha Rao\nPython LangGraph RAG\nGitHub: github.com/asha-rao", encoding="utf-8")

    resume = parse_resume(resume_path)

    assert resume.github_url == "https://github.com/asha-rao"
