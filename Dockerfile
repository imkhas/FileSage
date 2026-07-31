FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY organizer/ organizer/
COPY config.json ./

RUN pip install --no-cache-dir .

ENTRYPOINT ["file-organizer"]
