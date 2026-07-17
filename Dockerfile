# syntax=docker/dockerfile:1
# MoneyFlow full-stack image (Streamlit app; also runs the mock LLM service).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# curl is used by the container HEALTHCHECK and the app service healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root runtime user.
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app

# Copy the project (respecting .dockerignore) and install with the PostgreSQL
# driver. The heavy 'local-ai' extra is intentionally excluded — harness
# validation exercises the OpenAI-compatible provider against the mock server.
COPY . .
# Install with the Postgres driver, then drop any build byproducts so the image
# carries only a clean source tree (keeps linting/collection deterministic).
RUN pip install ".[postgres]" \
    && rm -rf build dist ./*.egg-info src/*.egg-info

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

HEALTHCHECK --interval=15s --timeout=5s --start-period=45s --retries=12 \
    CMD curl -fsS http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.headless", "true", \
     "--server.address", "0.0.0.0", \
     "--server.port", "8501"]
