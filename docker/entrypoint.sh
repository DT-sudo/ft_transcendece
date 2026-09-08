#!/usr/bin/env bash
set -euo pipefail

echo "==> Applying migrations"
python manage.py migrate --noinput

if [ "${SEED_DEMO_DATA:-1}" = "1" ]; then
  echo "==> Seeding demo data"
  python manage.py seed_demo
fi

echo "==> Starting application"
exec "$@"
