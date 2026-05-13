FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.3.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/opt/poetry/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

# IMPORTANT: build context must be the parent directory that
# contains BOTH DotSoundBot and DotSoundPrivateCore. Example:
#   docker build -f DotSoundBot/Dockerfile -t dotsoundbot .

WORKDIR /src

# poetry.lock pins directory url = "../DotSoundPrivateCore" relative to
# this WORKDIR (/src) -> must exist at /DotSoundPrivateCore.
COPY DotSoundPrivateCore /DotSoundPrivateCore
COPY DotSoundBot/pyproject.toml DotSoundBot/poetry.lock /src/

RUN poetry install --no-interaction --no-ansi --no-root --only main

COPY DotSoundBot/ /src/

# --exclude-editable strips the "-e /DotSoundPrivateCore" line that pip
# freeze would otherwise emit (and pip refuses to reinstall by path in
# the runtime stage). PrivateCore is reinstalled directly from source
# in the runtime stage below.
RUN poetry install --no-interaction --no-ansi --only main && \
    pip freeze --local --exclude-editable > /tmp/requirements-runtime.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup --system app && adduser --system --ingroup app app && \
    apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

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
