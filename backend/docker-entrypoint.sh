#!/bin/sh
set -eu

case "${1:-api}" in
  api)
    alembic upgrade head
    if [ -n "${WEBMAIL_BOOTSTRAP_ADMIN_EMAIL:-}" ] && [ -n "${WEBMAIL_BOOTSTRAP_ADMIN_PASSWORD:-}" ]; then
      python -m app.cli bootstrap-admin
    fi
    exec uvicorn app.main:app \
      --host 0.0.0.0 \
      --port 8000 \
      --proxy-headers \
      --forwarded-allow-ips '*' \
      --workers "${WEBMAIL_API_WORKERS:-2}"
    ;;
  migrate)
    exec alembic upgrade head
    ;;
  test)
    shift
    exec pytest "$@"
    ;;
  *)
    exec "$@"
    ;;
esac

