FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.3.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# No apt/build-essential: bot + PrivateCore main deps ship manylinux
# wheels (aiogram, aiohttp, pydantic, redis, httpx, ...). Compilers
# only bloat the builder and OOM/disk-out small deploy hosts that
# already ran a heavy backend image build in the same deploy.

# Poetry installed into an isolated venv at POETRY_HOME from a pinned
# PyPI version - no piping a remote installer script through the shell.
# POETRY_HOME is Poetry's data dir, so with virtualenvs disabled Poetry
# still installs project deps into the system site-packages (captured by
# pip freeze below). /opt/poetry/bin is kept off PATH so python3/pip stay
# the system interpreter.
RUN python3 -m venv /opt/poetry && \
    /opt/poetry/bin/pip install --no-cache-dir "poetry==${POETRY_VERSION}"

# IMPORTANT: build context must be the parent directory that
# contains BOTH DotSoundBot and DotSoundPrivateCore. Example:
#   docker build -f DotSoundBot/Dockerfile -t dotsoundbot .

WORKDIR /src

# poetry.lock pins directory url = "../DotSoundPrivateCore" relative to
# this WORKDIR (/src) -> must exist at /DotSoundPrivateCore.
COPY DotSoundPrivateCore /DotSoundPrivateCore
COPY DotSoundBot/pyproject.toml DotSoundBot/poetry.lock /src/

RUN /opt/poetry/bin/poetry install --no-interaction --no-ansi --no-root --only main

COPY DotSoundBot/ /src/

# --exclude-editable strips the "-e /DotSoundPrivateCore" line that pip
# freeze would otherwise emit (and pip refuses to reinstall by path in
# the runtime stage). PrivateCore is reinstalled directly from source
# in the runtime stage below.
RUN /opt/poetry/bin/poetry install --no-interaction --no-ansi --only main && \
    pip freeze --local --exclude-editable > /tmp/requirements-runtime.txt


FROM python:3.12-slim AS runtime

# MALLOC_ARENA_MAX=2 caps glibc per-thread malloc arenas so the
# long-running bot process doesn't fragment RSS across threads.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MALLOC_ARENA_MAX=2

RUN addgroup --system app && adduser --system --ingroup app app && \
    apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

WORKDIR /app

COPY --from=builder /tmp/requirements-runtime.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm -f /tmp/requirements.txt

# PrivateCore is installed without deps - all transitive deps are
# already pinned in requirements-runtime.txt above. Source tree is
# removed afterwards to keep the runtime image slim.
COPY DotSoundPrivateCore /tmp/DotSoundPrivateCore
RUN pip install --no-cache-dir --no-deps /tmp/DotSoundPrivateCore && \
    rm -rf /tmp/DotSoundPrivateCore

COPY DotSoundBot/ /app/

USER app

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8081/health || exit 1

CMD ["python", "main.py"]
