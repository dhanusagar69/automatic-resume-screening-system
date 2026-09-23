import json
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from resume_screening.pipeline import screen_directory, screen_input, write_results

ROOT = Path(__file__).parent
WEB_DIR = ROOT / "web"
RESUMES_DIR = ROOT / "resumes"
OUTPUT_PATH = ROOT / "output" / "results.json"

app = FastAPI(title="Shortlist Resume Screening API", version="0.1.0")
app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")


def empty_results() -> dict:
    return {"summary": {"total_resumes": 0, "successfully_parsed": 0, "eligible": 0, "rejected": 0, "failed_unreadable": 0}, "results": [], "failures": []}


def read_results() -> dict:
    if not OUTPUT_PATH.exists():
        return empty_results()
    return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))


@app.get("/", response_class=FileResponse)
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/app.js", response_class=FileResponse)
def javascript():
    return FileResponse(WEB_DIR / "app.js", media_type="text/javascript")


@app.get("/styles.css", response_class=FileResponse)
def stylesheet():
    return FileResponse(WEB_DIR / "styles.css", media_type="text/css")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/results")
def results():
    return read_results()


@app.get("/api/results/download")
def download_results():
    if not OUTPUT_PATH.exists():
        write_results(empty_results(), OUTPUT_PATH)
    return FileResponse(OUTPUT_PATH, media_type="application/json", filename="results.json")


@app.post("/api/screen")
async def screen(archive: UploadFile | None = File(default=None)):
    try:
        if archive is None:
            payload = screen_directory(RESUMES_DIR)
        else:
            if not archive.filename or not archive.filename.lower().endswith(".zip"):
                raise HTTPException(status_code=400, detail="Choose a .zip archive.")
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(await archive.read())
            try:
                payload = screen_input(temporary_path)
            finally:
                temporary_path.unlink(missing_ok=True)
        write_results(payload, OUTPUT_PATH)
        return JSONResponse(payload)
    except HTTPException:
        raise
    except Exception as exc:
        return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web_server:app", host="127.0.0.1", port=8000, reload=False)
