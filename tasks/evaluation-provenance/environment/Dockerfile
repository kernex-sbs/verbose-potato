FROM python:3.13.14-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl jq postgresql-client redis-tools \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app
COPY SPEC.md /app/SPEC.md
COPY fixtures/ /app/fixtures/
COPY evalstack/ /app/evalstack/
COPY entrypoint.sh /usr/local/bin/evalstack-entrypoint

RUN chmod +x /usr/local/bin/evalstack-entrypoint /app/evalstack/evalctl \
    && ln -s /app/evalstack/evalctl /usr/local/bin/evalctl

CMD ["/usr/local/bin/evalstack-entrypoint"]
