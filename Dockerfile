# syntax=docker/dockerfile:1.7
FROM python:3.12.11-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install .

FROM python:3.12.11-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN groupadd --system --gid 10001 clientrevive \
    && useradd --system --uid 10001 --gid clientrevive --home-dir /app clientrevive \
    && mkdir -p /app/state /app/data/artifacts \
    && chown -R clientrevive:clientrevive /app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=clientrevive:clientrevive data ./data
USER clientrevive
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import json,urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3); assert json.load(r)['status']=='healthy'" || exit 1
CMD ["clientrevive"]
