FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock* ./
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
RUN uv sync
RUN uv pip install --python /opt/venv/bin/python --no-cache flet-cli==0.86.5 flet-web==0.86.5 flet-desktop==0.86.5
COPY . .
EXPOSE 8550
ENV PATH=/opt/venv/bin:$PATH
ENV PYTHONPATH=/app
CMD ["flet", "run", "--web", "--port", "8550", "--host", "0.0.0.0", "app/main.py"]
