from resume_screening.models import LLMAnalysis, Resume
from resume_screening.scoring import eligibility, score_resume


def test_java_only_profile_is_rejected():
    resume = Resume(path="java.txt", text="Asha Rao\nJava React Spring Boot")
    eligible, reasons, _ = eligibility(resume)
    assert not eligible
    assert "No evidence of Python stack" in reasons


def test_python_ai_profile_is_eligible_and_explainable():
    resume = Resume(path="ai.txt", text="Asha Rao\nBuilt a stateful LangGraph RAG agent with Python and FastAPI. Added embeddings, tool calling, PostgreSQL, Docker, pytest and evaluation pipeline.")
    result = score_resume(resume)
    assert result.eligible
    assert result.total_score > 50
    assert result.score_breakdown["ai_project_depth"] >= 30
    assert result.evidence


def test_shallow_ai_profile_is_penalized():
    resume = Resume(path="thin.txt", text="Sam Lee\nPython\nAI chatbot using an LLM API")
    result = score_resume(resume)
    assert result.eligible
    assert result.total_score < 50
    assert result.concerns


def test_llm_analysis_is_bounded_and_used_for_project_depth():
    resume = Resume(path="llm.txt", text="Sam Lee\nPython and LangGraph agent with retrieval")
    result = score_resume(resume, llm=LLMAnalysis(status="ok", project_depth_score=40, shallow_project=False, summary="Stateful retrieval agent", evidence=["Built retrieval agent"]))
    assert result.llm_status == "ok"
    assert result.project_summary == "Stateful retrieval agent"
    assert 0 <= result.score_breakdown["ai_project_depth"] <= 40

