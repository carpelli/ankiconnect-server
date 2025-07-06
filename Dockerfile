FROM python:3.12-slim as builder

RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.12-slim

RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY . /app/

# Create data directory and set permissions
RUN mkdir -p /data && chown -R app:app /app /data

# Switch to non-root user
USER app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV ANKICONNECT_HOST=0.0.0.0
ENV ANKICONNECT_PORT=8765
ENV ANKICONNECT_LOG_LEVEL="INFO"

# Expose port
EXPOSE 8765

# Health check
HEALTHCHECK CMD python -c "import requests; requests.post('http://localhost:8765')" || exit 1

# Run the application
CMD ["python", "-m", "app.server", "-b", "/data", "--create"]
