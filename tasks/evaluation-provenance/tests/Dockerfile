FROM python:3.13.14-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

COPY requirements.txt /tmp/verifier-requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/verifier-requirements.txt

COPY . /tests/
RUN mkdir -p /app /tmp

WORKDIR /app
