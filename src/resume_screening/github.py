import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import GitHubResult


def enrich(github_url: str | None) -> GitHubResult:
    if not github_url:
        return GitHubResult(status="not_available", summary="No public GitHub profile found.")
    match = re.search(r"github\.com/([^/]+)", github_url, re.I)
    if not match:
        return GitHubResult(status="invalid", summary="GitHub URL could not be parsed.")
    username = match.group(1)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "resume-screening"}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    try:
        profile = _get(f"https://api.github.com/users/{username}", headers)
        repos = _get(f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated", headers)
        public_repos = int(profile.get("public_repos", 0))
        recent = sum(1 for repo in repos if repo.get("fork") is False and repo.get("pushed_at"))
        relevant = sum(1 for repo in repos if any(word in (repo.get("name", "") + " " + (repo.get("description") or "")).lower() for word in ["python", "ai", "agent", "rag", "llm"]))
        score = min(5, recent // 3) + min(5, relevant + (1 if public_repos >= 3 else 0))
        return GitHubResult(status="enriched", score=min(10, score), summary=f"{public_repos} public repositories; {recent} recently updated non-forks; {relevant} Python/AI-relevant.")
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as exc:
        return GitHubResult(status="failed", summary=f"GitHub enrichment unavailable: {type(exc).__name__}.")


def _get(url: str, headers: dict[str, str]):
    request = Request(url, headers=headers)
    with urlopen(request, timeout=8) as response:
        import json

        return json.loads(response.read().decode("utf-8"))
