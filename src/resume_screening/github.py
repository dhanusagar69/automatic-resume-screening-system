import os
import re
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import github_recency_days
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
        score, summary = score_repositories(repos, github_recency_days())
        return GitHubResult(status="enriched", score=score, summary=f"{public_repos} public repositories; {summary}")
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return GitHubResult(status="failed", summary=f"GitHub enrichment unavailable: {type(exc).__name__}.")


def score_repositories(repositories: list[dict], recency_days: int, now: datetime | None = None) -> tuple[int, str]:
    """Return an explainable 0-10 score for original repositories."""
    if not isinstance(repositories, list):
        raise ValueError("GitHub repositories response must be a list")
    current_time = now or datetime.now(timezone.utc)
    cutoff = current_time - timedelta(days=max(1, recency_days))
    original_repositories = [repo for repo in repositories if isinstance(repo, dict) and repo.get("fork") is False]
    recent_repositories = []
    maintained_repositories = []
    relevant_repositories = []
    for repo in original_repositories:
        pushed_at = _parse_github_time(repo.get("pushed_at"))
        if pushed_at is not None:
            maintained_repositories.append(repo)
            if pushed_at >= cutoff:
                recent_repositories.append(repo)
        description = f"{repo.get('name', '')} {repo.get('description') or ''}".lower()
        if any(term in description for term in ["python", "ai", "agent", "rag", "llm"]):
            relevant_repositories.append(repo)
    recent_points = min(5, len(recent_repositories) + (1 if recent_repositories else 0))
    maintained_points = min(3, len(maintained_repositories)) + min(2, len(relevant_repositories))
    score = min(10, recent_points + maintained_points)
    details = []
    if recent_repositories:
        details.append(f"active within last {recency_days} days; {len(recent_repositories)} recently updated repositories")
    else:
        details.append(f"no repository activity within last {recency_days} days")
    if relevant_repositories:
        details.append(f"{len(relevant_repositories)} Python/AI repositories")
    if maintained_repositories:
        details.append(f"{len(maintained_repositories)} maintained original repositories")
    return score, "; ".join(details) + f"; score {score}/10"


def _parse_github_time(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _get(url: str, headers: dict[str, str]):
    request = Request(url, headers=headers)
    with urlopen(request, timeout=8) as response:
        import json

        return json.loads(response.read().decode("utf-8"))
