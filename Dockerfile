FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml requirements.txt README.md ./
COPY src ./src
COPY main.py web_server.py ./
COPY web ./web
COPY resumes ./resumes

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "web_server:app", "--host", "0.0.0.0", "--port", "8000"]
