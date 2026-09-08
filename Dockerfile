# Demo/development image: runs the Django dev server with DEBUG on so the
# one-click demo logins work. Not intended as a production image.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user; /app/data holds the SQLite file (mounted as a volume).
RUN useradd --create-home app \
    && mkdir -p /app/data \
    && chown -R app:app /app
USER app

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
