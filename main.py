import argparse
from pathlib import Path

from resume_screening.pipeline import screen_input, write_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Screen and rank resumes for a Python/AI SDE internship.")
    parser.add_argument("--input", required=True, type=Path, help="Resume directory or .zip archive containing PDF, DOCX, or TXT resumes")
    parser.add_argument("--output", default=Path("output/results.json"), type=Path, help="Output JSON path")
    args = parser.parse_args()
    if not args.input.is_dir() and not (args.input.is_file() and args.input.suffix.lower() == ".zip"):
        parser.error(f"Input must be a directory or .zip archive: {args.input}")
    payload = screen_input(args.input)
    write_results(payload, args.output)
    print(f"Screened {payload['summary']['total_resumes']} resumes; wrote {args.output}")


if __name__ == "__main__":
    main()
