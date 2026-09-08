FROM python:3.14-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
RUN uv sync --frozen --no-install-project
COPY . .
EXPOSE 8550
ENV PATH=/opt/venv/bin:$PATH
ENV PYTHONPATH=/app
# Default target API; docker-compose overrides this with http://api:8000.
ENV ASCEND_API_URL=https://backend-five-swart-37.vercel.app
CMD ["flet", "run", "--web", "--port", "8550", "--host", "0.0.0.0", "app/main.py"]
