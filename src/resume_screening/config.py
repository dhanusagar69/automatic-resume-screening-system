import os


DEFAULT_GITHUB_RECENCY_DAYS = 90


def github_recency_days() -> int:
    try:
        return max(1, int(os.getenv("GITHUB_RECENCY_DAYS", DEFAULT_GITHUB_RECENCY_DAYS)))
    except (TypeError, ValueError):
        return DEFAULT_GITHUB_RECENCY_DAYS
