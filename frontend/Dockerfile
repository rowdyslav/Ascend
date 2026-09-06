FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock* ./
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
RUN uv sync
COPY . .
EXPOSE 8550
ENV PATH=/opt/venv/bin:$PATH
CMD ["flet", "run", "--web", "--port", "8550", "--host", "0.0.0.0", "main.py"]
