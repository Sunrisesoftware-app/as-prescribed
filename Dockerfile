FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY asprescribed ./asprescribed
COPY data ./data

# Keys come from the environment (compose: env_file .env); nothing is baked into the image.
EXPOSE 8300
CMD ["uv", "run", "--no-sync", "uvicorn", "asprescribed.main:app", "--host", "0.0.0.0", "--port", "8300"]
