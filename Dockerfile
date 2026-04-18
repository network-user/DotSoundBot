FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/opt/poetry/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

# IMPORTANT: build context must be the parent directory that
# contains BOTH DotSoundBot and DotSoundPrivateCore. Example:
#   docker build -f DotSoundBot/Dockerfile -t dotsoundbot .
# Or in docker-compose:
#   build:
#     context: ..
#     dockerfile: DotSoundBot/Dockerfile

WORKDIR /app

COPY DotSoundPrivateCore /private_core
COPY DotSoundBot/pyproject.toml DotSoundBot/poetry.lock ./

# Re-point the relative path dependency to the copied location
RUN sed -i 's|path = "../DotSoundPrivateCore"|path = "/private_core"|' \
    pyproject.toml

RUN poetry install --no-interaction --no-ansi --no-root --only main

COPY DotSoundBot/ .

RUN poetry install --no-interaction --no-ansi --only main

CMD ["python", "main.py"]
