# Demo/development image: runs the Django dev server with DEBUG on so the
# one-click demo logins work. Not intended as a production image.

# ── Stage 1: build the React/Tailwind bundle ──
FROM node:22-slim AS frontend

WORKDIR /build

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/vite.config.js ./
COPY frontend/src ./src
RUN npm run build

# ── Stage 2: Django ──
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend /build/dist ./frontend/dist

# Run as a non-root user; /app/data holds the SQLite file (mounted as a volume).
RUN useradd --create-home app \
    && mkdir -p /app/data \
    && chown -R app:app /app
USER app

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
# nginx proxies /static/ to Django too; --insecure keeps runserver serving the
# bundle when DEBUG=0 instead of answering 404 and leaving the page blank.
CMD ["python", "manage.py", "runserver", "--insecure", "0.0.0.0:8000"]
