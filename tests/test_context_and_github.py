from datetime import datetime, timezone

from resume_screening.github import score_repositories
from resume_screening.models import Resume
from resume_screening.scoring import eligibility, score_resume

NOW = datetime(2026, 9, 23, tzinfo=timezone.utc)


def test_python_project_evidence_passes_python_requirement():
    resume = Resume(path="project.txt", text="Projects:\nBuilt a FastAPI backend in Python for a candidate screening service.")
    eligible, reasons, _ = eligibility(resume)
    assert not eligible
    assert "No evidence of Python stack" not in reasons
    assert "No AI/agentic project evidence" in reasons


def test_incidental_python_mention_does_not_count_as_strong_evidence():
    resume = Resume(path="objective.txt", text="Career Objective:\nInterested in learning Python and AI.")
    eligible, reasons, _ = eligibility(resume)
    assert not eligible
    assert "No evidence of Python stack" in reasons


def test_rag_project_evidence_passes_ai_requirement():
    resume = Resume(path="rag.txt", text="Experience:\nImplemented a RAG pipeline with embeddings, vector search, and tool calling using Python.")
    eligible, reasons, _ = eligibility(resume)
    assert eligible
    assert "No AI/agentic project evidence" not in reasons


def test_interested_in_ai_does_not_pass_ai_requirement():
    resume = Resume(path="interest.txt", text="Interests:\nInterested in AI and learning about LLMs.")
    eligible, reasons, _ = eligibility(resume)
    assert not eligible
    assert "No AI/agentic project evidence" in reasons


def test_java_react_candidate_with_python_ai_evidence_remains_eligible():
    resume = Resume(path="fullstack.txt", text="Skills:\nJava React Spring Boot Python\nProjects:\nBuilt a Python LangGraph agent with RAG retrieval.")
    result = score_resume(resume)
    assert result.eligible
    assert result.total_score <= 100


def test_recent_original_repository_receives_activity_points():
    score, summary = score_repositories(
        [{"name": "agent-api", "description": "Python RAG service", "fork": False, "pushed_at": "2026-09-01T00:00:00Z"}],
        recency_days=90,
        now=NOW,
    )
    assert score >= 2
    assert "active within last 90 days" in summary


def test_old_repository_gets_no_recent_activity_points():
    score, summary = score_repositories(
        [{"name": "old-api", "description": "Python service", "fork": False, "pushed_at": "2025-01-01T00:00:00Z"}],
        recency_days=90,
        now=NOW,
    )
    assert "no repository activity within last 90 days" in summary
    assert score <= 5


def test_relevant_repositories_receive_relevance_points_and_forks_are_excluded_from_maintained_count():
    score, summary = score_repositories(
        [
            {"name": "python-agent", "description": "LLM agent", "fork": False, "pushed_at": "2025-01-01T00:00:00Z"},
            {"name": "forked-rag", "description": "RAG", "fork": True, "pushed_at": "2026-09-01T00:00:00Z"},
        ],
        recency_days=90,
        now=NOW,
    )
    assert score >= 2
    assert "1 Python/AI repositories" in summary
    assert "1 maintained original repositories" in summary


def test_github_score_is_always_capped_at_ten():
    repositories = [{"name": f"python-agent-{index}", "description": "AI Python RAG", "fork": False, "pushed_at": "2026-09-22T00:00:00Z"} for index in range(100)]
    score, _ = score_repositories(repositories, recency_days=90, now=NOW)
    assert score <= 10


def test_missing_github_does_not_reject_candidate():
    result = score_resume(Resume(path="no-github.txt", text="Built a Python LangGraph RAG service."))
    assert result.eligible
    assert result.github_status == "not_available"
