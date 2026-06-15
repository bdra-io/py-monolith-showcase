# =====================================================================
# STAGE 1: Compilation, Linting, & Chaos Validation Gate
# =====================================================================
FROM python:3.12-slim AS verification-gate

WORKDIR /workspace

# Install system and python dependencies required for testing
COPY requirements.txt* ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn aiosqlite click mypy pydantic pytest pytest-archon pytest-asyncio httpx httpx2

# Copy the entire codebase and test matrix into the gate workspace
COPY app/ ./app/
COPY tests/ ./tests/
COPY bdracheck.py pyproject.toml ./

# Only run strict type validation on production source code modules
RUN python -m mypy app bdracheck.py

# RUN THE CHAOS, RESILIENCY, AND INVARIANT TESTS
RUN python -m pytest tests/ -v

# =====================================================================
# STAGE 2: Secure, Lightweight Production Runtime
# =====================================================================
FROM python:3.12-slim AS production

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn aiosqlite click pydantic httpx

COPY --from=verification-gate /workspace/app ./app

RUN useradd -u 10011 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]