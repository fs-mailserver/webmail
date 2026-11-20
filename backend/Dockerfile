FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first for better layer caching.
COPY pyproject.toml ./
RUN mkdir -p app && touch app/__init__.py \
    && pip install ".[dev]" \
    && rm -rf app build *.egg-info

COPY . .
RUN chmod +x docker-entrypoint.sh \
    && mkdir -p /app/storage/attachments /app/storage/eml

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["api"]

