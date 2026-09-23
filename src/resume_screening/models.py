from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Resume:
    path: str
    text: str
    name: str = "Unknown candidate"
    email: str | None = None
    github_url: str | None = None
    skills: list[str] = field(default_factory=list)


@dataclass
class GitHubResult:
    status: str
    score: int = 0
    summary: str = ""


@dataclass
class LLMAnalysis:
    status: str = "not_configured"
    project_depth_score: int = 0
    shallow_project: bool = False
    shallow_penalty: int = 0
    summary: str = ""
    evidence: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)


@dataclass
class CandidateResult:
    candidate_name: str
    source_file: str
    eligible: bool
    total_score: int = 0
    score_breakdown: dict[str, int] = field(default_factory=dict)
    matched_skills: list[str] = field(default_factory=list)
    project_summary: str = ""
    github_summary: str = ""
    github_status: str = "not_available"
    llm_status: str = "not_configured"
    strengths: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    rejection_reasons: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    error: str | None = None
    rank: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
