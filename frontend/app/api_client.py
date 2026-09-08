import os
from typing import Any

import httpx

from app.utils.logger import logger

# Static GitHub Pages build runs in the browser (Pyodide) where env vars don't
# exist, so the production API URL is the default. Local dev overrides it:
#   ASCEND_API_URL=http://localhost:8000 flet run --web app/main.py
# Docker Compose sets http://api:8000 automatically.
API_URL = os.getenv("ASCEND_API_URL", "https://backend-five-swart-37.vercel.app")


class ApiError(RuntimeError):
    pass


class ApiClient:
    def __init__(self) -> None:
        self.base_url = API_URL.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=10)

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = self.client.request(method, path, **kwargs)
            logger.info("API %s %s -> %s", method, path, response.status_code)
            if response.status_code >= 400:
                detail = response.json().get("detail", response.text)
                if isinstance(detail, dict):
                    detail = detail.get("message", str(detail))
                logger.error("API %s %s failed (%s): %s", method, path, response.status_code, detail)
                raise ApiError(str(detail))
            return response.json()
        except httpx.HTTPError as exc:
            logger.error("API %s %s failed: %s", method, path, exc)
            raise ApiError(f"Нет соединения с API: {exc}") from exc

    def get(self, path: str, params: dict | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, data: dict | None = None) -> Any:
        return self.request("POST", path, json=data or {})

    def put(self, path: str, data: dict | None = None) -> Any:
        return self.request("PUT", path, json=data or {})

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)
