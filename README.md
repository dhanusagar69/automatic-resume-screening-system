# AI Resume Screening & Ranking

An explainable, CLI-first pipeline for screening resumes against the Python + AI/agentic SDE intern brief. It supports PDF, DOCX, TXT, and Markdown files and always emits machine-readable JSON.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Run

```powershell
py main.py --input .\resumes --output .\output\results.json
# Or process a ZIP archive directly
py main.py --input .\candidate-resumes.zip --output .\output\results.json
```

The `--input` value may be a folder or ZIP file. ZIP paths are checked for path traversal before extraction, supported resumes are processed from a temporary directory, and the temporary files are removed after the run.

## Dashboard

Start the local review dashboard from the project root:

```powershell
py web_server.py
```

Open http://127.0.0.1:8000. The dashboard reads the generated results. Choose a ZIP archive to screen that upload, or leave it empty to rerun against `./resumes`; then click **Run screening**. Stop it with `Ctrl+C`.

## Deploy

The dashboard is a FastAPI web service and can be deployed to Render using the included `render.yaml`:

```text
Build command: pip install -r requirements.txt
Start command: uvicorn web_server:app --host 0.0.0.0 --port $PORT
Health check: /health
```

Or build and run it with Docker:

```powershell
docker build -t shortlist-screening .
docker run --rm -p 8000:8000 shortlist-screening
```

Configure `GEMINI_API_KEY` as a deployment environment variable, never in the repository.

`GITHUB_TOKEN` is optional and may be loaded in the shell from `.env.example`. To enable structured Gemini enrichment, set `GEMINI_API_KEY`:

```powershell
$env:GEMINI_API_KEY="your-gemini-api-key"
$env:GEMINI_MODEL="gemini-2.0-flash"
```

The model is used only for project-depth judgment and evidence-backed summaries. Hard eligibility remains deterministic, JSON fields are validated and bounded, and missing keys, failed calls, or malformed responses fall back to the heuristic scorer.

## Design Decisions

- Hard eligibility is deterministic and stays outside any LLM: evidence for both Python and a meaningful AI/agentic concept is required.
- Ranking favors project evidence and implementation depth over skill-list mentions. Thin LLM wrappers receive a penalty and every result carries matched evidence lines.
- GitHub enrichment uses two public API calls per profile, is capped at 10 points, and records `failed` or `not_available` instead of blocking screening.
- Parsing is isolated per file, so malformed documents become batch failures while other resumes continue through the pipeline.
- The optional Gemini adapter in `llm.py` uses structured JSON, clamps scores, treats resume text as untrusted data, and stays behind the deterministic scoring contract.

## Output

The JSON contains a batch summary, ranked eligible candidates, rejected candidates with explicit reasons, score breakdowns, evidence, GitHub status, and unreadable-file failures.

## If I Had More Time

- Add an OpenAI-compatible structured extraction adapter with Pydantic validation and retry limits.
- Add persistent per-run GitHub caching and bounded concurrency for larger batches.
- Add OCR for image-only PDFs and richer section-aware project extraction.
- Add integration fixtures for real PDF/DOCX parsing and API responses.
