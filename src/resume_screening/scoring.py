import re

from .models import CandidateResult, GitHubResult, LLMAnalysis, Resume

PYTHON_TERMS = ["python", "fastapi", "django", "flask", "pytest", "asyncio"]
AI_TERMS = ["langchain", "langgraph", "llamaindex", "rag", "retrieval augmented", "embedding", "vector search", "agentic", "ai agent", "tool calling", "multi-agent", "google adk", "llm", "large language model"]
SKILL_TERMS = PYTHON_TERMS + AI_TERMS + ["postgresql", "redis", "docker", "gcp", "react", "next.js", "kafka", "graphql"]
DEPTH_TERMS = ["pipeline", "evaluation", "evals", "orchestration", "stateful", "workflow", "retrieval", "vector", "tool", "queue", "caching", "cache", "observability", "testing", "concurrency", "async", "failure handling"]
STRONG_SECTIONS = ("project", "experience", "work", "internship", "employment", "implementation", "backend", "research")
SKILL_SECTIONS = ("skill", "technology", "tech stack", "competenc", "proficien")
WEAK_SECTIONS = ("objective", "interest", "hobby", "career goal", "currently learning", "learning")
IMPLEMENTATION_VERBS = ("built", "developed", "implemented", "designed", "created", "deployed", "integrated", "trained", "engineered", "automated", "added", "used", "using", "wrote")
INCIDENTAL_PHRASES = ("interested in", "currently learning", "want to learn", "learning about", "familiar with")


def _has_term(text: str, term: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text.lower()) is not None


def matched_skills(text: str) -> list[str]:
    return [term for term in SKILL_TERMS if _has_term(text, term)]


def _section_kind(heading: str) -> str:
    heading = heading.lower()
    if any(term in heading for term in WEAK_SECTIONS):
        return "weak"
    if any(term in heading for term in STRONG_SECTIONS):
        return "strong"
    if any(term in heading for term in SKILL_SECTIONS):
        return "skill"
    return "other"


def _contextual_lines(text: str) -> list[tuple[str, str]]:
    current_section = "other"
    contextual = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        normalized = line.strip(" :-|\t").lower()
        if len(normalized) <= 55 and (normalized.endswith(":") or normalized in {"projects", "experience", "skills", "interests", "objective"}):
            current_section = _section_kind(normalized.rstrip(":"))
            continue
        contextual.append((line, current_section))
    return contextual


def _evidence_lines(text: str, terms: list[str]) -> list[str]:
    return [line[:220] for line, section in _contextual_lines(text) if section != "weak" and any(_has_term(line, term) for term in terms)][:4]


def _requirement_evidence(text: str, terms: list[str]) -> tuple[bool, list[str]]:
    evidence = []
    for line, section in _contextual_lines(text):
        if not any(_has_term(line, term) for term in terms) or section == "weak":
            continue
        lower_line = line.lower()
        if any(phrase in lower_line for phrase in INCIDENTAL_PHRASES):
            continue
        has_implementation_language = any(verb in lower_line for verb in IMPLEMENTATION_VERBS)
        term_count = sum(_has_term(lower_line, term) for term in terms)
        all_signal_count = sum(_has_term(lower_line, term) for term in SKILL_TERMS)
        standalone_skill = lower_line.strip() in terms
        if section == "strong" or section == "skill" or has_implementation_language or term_count >= 2 or all_signal_count >= 2 or standalone_skill:
            evidence.append(line[:220])
    return bool(evidence), evidence[:4]


def eligibility(resume: Resume) -> tuple[bool, list[str], list[str]]:
    python_found, _ = _requirement_evidence(resume.text, PYTHON_TERMS)
    ai_found, _ = _requirement_evidence(resume.text, AI_TERMS)
    reasons = []
    if not python_found:
        reasons.append("No evidence of Python stack")
    if not ai_found:
        reasons.append("No AI/agentic project evidence")
    return not reasons, reasons, matched_skills(resume.text)


def _evidence(text: str, terms: list[str]) -> list[str]:
    return _evidence_lines(text, terms)


def score_resume(resume: Resume, github: GitHubResult | None = None, llm: LLMAnalysis | None = None) -> CandidateResult:
    eligible, rejection_reasons, skills = eligibility(resume)
    result = CandidateResult(candidate_name=resume.name, source_file=resume.path, eligible=eligible, matched_skills=skills, rejection_reasons=rejection_reasons)
    if not eligible:
        result.project_summary = "Not ranked because the hard eligibility filter failed."
        return result

    text = resume.text.lower()
    ai_evidence = _evidence(text, AI_TERMS)
    python_evidence = _evidence(text, PYTHON_TERMS + ["postgresql", "redis"])
    depth_hits = sum(_has_term(text, term) for term in DEPTH_TERMS)
    ai_depth = min(40, 19 + len(ai_evidence) * 5 + min(8, sum(_has_term(text, term) for term in DEPTH_TERMS[:8]) * 2))
    if len(ai_evidence) <= 1 and not any(_has_term(text, term) for term in ["workflow", "retrieval", "tool calling", "evaluation"]):
        ai_depth = max(5, ai_depth - 12)
        result.concerns.append("AI experience may be a thin API wrapper")
    backend_terms = ["python", "fastapi", "django", "flask", "async", "postgresql", "redis"]
    backend = min(30, 10 + sum(_has_term(text, term) for term in backend_terms) * 3 + min(7, len(python_evidence)))
    cloud = min(15, sum(_has_term(text, term) for term in ["gcp", "docker", "kubernetes", "deployment", "react", "next.js"]) * 3)
    engineering = min(5, depth_hits // 2)
    github_result = github or GitHubResult(status="not_available")
    result.score_breakdown = {"ai_project_depth": ai_depth, "python_backend": backend, "cloud_fullstack": cloud, "github": github_result.score, "engineering_depth": engineering}
    result.total_score = sum(result.score_breakdown.values())
    result.github_status = github_result.status
    result.github_summary = github_result.summary
    result.llm_status = llm.status if llm else "not_configured"
    result.evidence = ai_evidence + python_evidence
    result.project_summary = ai_evidence[0] if ai_evidence else "Python and AI evidence found, but project detail is limited."
    if llm and llm.status == "ok":
        ai_depth = max(0, min(40, round((ai_depth + llm.project_depth_score) / 2) - llm.shallow_penalty))
        result.score_breakdown["ai_project_depth"] = ai_depth
        result.project_summary = llm.summary or result.project_summary
        result.evidence = (llm.evidence + result.evidence)[:6]
        result.strengths.extend(llm.strengths)
        result.concerns.extend(llm.concerns)
        if llm.shallow_project and "AI experience may be a thin API wrapper" not in result.concerns:
            result.concerns.append("AI experience may be a thin API wrapper")
        result.total_score = sum(result.score_breakdown.values())
    result.strengths = list(result.strengths)
    if ai_depth >= 30:
        result.strengths.append("Strong AI/agentic project evidence")
    if backend >= 22:
        result.strengths.append("Solid Python/backend evidence")
    if cloud >= 9:
        result.strengths.append("End-to-end or deployment experience")
    if not result.strengths:
        result.concerns.append("Limited implementation detail in resume")
    return result
