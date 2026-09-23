import json
from pathlib import Path

from .archives import input_directory
from .github import enrich
from .llm import analyze_resume
from .models import CandidateResult, LLMAnalysis
from .parsers import discover_resumes, parse_resume
from .scoring import eligibility, score_resume


def screen_directory(input_dir: Path) -> dict:
    results: list[CandidateResult] = []
    failed = []
    paths = discover_resumes(input_dir)
    for path in paths:
        try:
            resume = parse_resume(path)
            is_eligible, _, _ = eligibility(resume)
            llm = analyze_resume(resume) if is_eligible else LLMAnalysis()
            results.append(score_resume(resume, enrich(resume.github_url), llm))
        except Exception as exc:
            failed.append({"source_file": str(path), "error": f"{type(exc).__name__}: {exc}"})
    results.sort(key=lambda item: (item.eligible, item.total_score), reverse=True)
    rank = 0
    for result in results:
        if result.eligible:
            rank += 1
            result.rank = rank
    return {
        "summary": {"total_resumes": len(paths), "successfully_parsed": len(results), "eligible": sum(item.eligible for item in results), "rejected": sum(not item.eligible for item in results), "failed_unreadable": len(failed)},
        "results": [item.to_dict() for item in results],
        "failures": failed,
    }


def screen_input(input_path: Path) -> dict:
    for input_dir in input_directory(input_path):
        return screen_directory(input_dir)
    raise ValueError(f"Could not read input: {input_path}")


def write_results(payload: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
