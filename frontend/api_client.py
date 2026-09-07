import os
from typing import Any

import httpx

try:
    from api_config import API_URL
except ImportError:
    API_URL = os.getenv("ASCEND_API_URL", "http://localhost:8000")


class ApiError(RuntimeError):
    pass


class ApiClient:
    def __init__(self) -> None:
        self.base_url = API_URL.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=10)

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = self.client.request(method, path, **kwargs)
            if response.status_code >= 400:
                detail = response.json().get("detail", response.text)
                if isinstance(detail, dict):
                    detail = detail.get("message", str(detail))
                raise ApiError(str(detail))
            return response.json()
        except httpx.HTTPError as exc:
            raise ApiError(f"Нет соединения с API: {exc}") from exc

    def get(self, path: str, params: dict | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, data: dict | None = None) -> Any:
        return self.request("POST", path, json=data or {})

    def put(self, path: str, data: dict | None = None) -> Any:
        return self.request("PUT", path, json=data or {})

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)
