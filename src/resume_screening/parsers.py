import re
from pathlib import Path

from .models import Resume

SUPPORTED = {".pdf", ".docx", ".txt", ".md"}
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
GITHUB_RE = re.compile(r"(?<![\w.-])(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9-]+/?", re.I)


def _pdf_text(path: Path) -> str:
    from pypdf import PdfReader

    return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def _docx_text(path: Path) -> str:
    from docx import Document

    document = Document(str(path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return _pdf_text(path)
    if path.suffix.lower() == ".docx":
        return _docx_text(path)
    return path.read_text(encoding="utf-8", errors="replace")


def _candidate_name(text: str, path: Path) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:8]:
        if "@" not in line and not GITHUB_RE.search(line) and 2 <= len(line.split()) <= 5:
            return line
    return path.stem.replace("_", " ").replace("-", " ").title()


def parse_resume(path: Path) -> Resume:
    text = extract_text(path)
    email_match = EMAIL_RE.search(text)
    github_match = GITHUB_RE.search(text)
    github_url = github_match.group(0).rstrip("/") if github_match else None
    if github_url and not github_url.lower().startswith(("http://", "https://")):
        github_url = f"https://{github_url}"
    return Resume(
        path=str(path),
        text=text,
        name=_candidate_name(text, path),
        email=email_match.group(0) if email_match else None,
        github_url=github_url,
    )


def discover_resumes(directory: Path) -> list[Path]:
    return sorted(path for path in directory.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED)
