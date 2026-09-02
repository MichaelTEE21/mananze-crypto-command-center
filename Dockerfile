# MCCC production container — Streamlit long-running server.
# Primary public host: Render (Docker). Not compatible with Vercel serverless.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MCCC_DATA_DIR=/data \
    PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app.py START.ps1 START.bat pytest.ini ./
COPY scripts ./scripts
COPY src ./src
COPY pages ./pages
COPY content ./content
COPY .streamlit ./.streamlit

RUN mkdir -p /data \
    && useradd -m -u 10001 mccc \
    && chown -R mccc:mccc /app /data \
    && chmod +x /app/scripts/start.sh

USER mccc
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT:-8501}/_stcore/health || exit 1

# Persist SQLite via disk mount at /data (set MCCC_DATA_DIR=/data)
CMD ["/app/scripts/start.sh"]
