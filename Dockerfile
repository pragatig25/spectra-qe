###############################################################################
# Stage 1: Build frontend
###############################################################################
FROM node:20-slim AS frontend-build

WORKDIR /app/ui

COPY ui/package.json ui/package-lock.json ./
RUN npm ci

COPY ui/ ./
RUN npm run build

###############################################################################
# Stage 2: Python backend (base)
###############################################################################
FROM python:3.10-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    fastapi uvicorn python-multipart \
    langchain langchain-openai langchain-anthropic langchain-community \
    openai anthropic pydantic pydantic-settings pyyaml click structlog \
    python-dotenv numpy httpx rich jinja2 eval_type_backport

COPY qe_platform/ ./qe_platform/
COPY demo/ ./demo/

# Copy built frontend
COPY --from=frontend-build /app/ui/dist ./ui/dist

RUN pip install --no-cache-dir -e .

###############################################################################
# Stage 3: Test runner (docker compose up test)
###############################################################################
FROM base AS test

RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov pytest-mock

COPY tests/ ./tests/

CMD ["python", "-m", "pytest", "tests/unit/", "-v"]

###############################################################################
# Stage 4: Production app (default — must be last)
###############################################################################
FROM base AS app

EXPOSE 8000

CMD ["uvicorn", "qe_platform.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
