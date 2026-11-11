"""HTTP clients for the two REST services. The BFF owns no database."""
from typing import Any

import httpx

from app import config


class RestError(Exception):
    """A REST error translated into something the GraphQL layer can return."""

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def _raise_for_response(response: httpx.Response) -> None:
    if response.status_code < 400:
        return
    try:
        error = response.json()["error"]
        raise RestError(response.status_code, error.get("code", "http_error"),
                        error.get("message", f"HTTP {response.status_code}"))
    except (ValueError, KeyError, TypeError):
        raise RestError(response.status_code, "http_error", f"HTTP {response.status_code}")


async def _request(method: str, url: str, token: str, **kwargs: Any) -> Any:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.request(method, url, headers={"Authorization": f"Bearer {token}"}, **kwargs)
    except httpx.HTTPError as exc:
        raise RestError(503, "service_unavailable", f"Cannot reach {url}") from exc
    _raise_for_response(response)
    return response.json()


class PlacementClient:
    async def get(self, placement_id: str, token: str) -> dict:
        return await _request("GET", f"{config.placement_service_url()}/v1/placements/{placement_id}", token)


class LogbookClient:
    async def list_entries(self, token: str, *, placement_id: str | None = None,
                           status: str | None = None, page: int = 1, page_size: int = 10) -> dict:
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if placement_id:
            params["placementId"] = placement_id
        if status:
            params["status"] = status
        return await _request("GET", f"{config.logbook_service_url()}/v1/entries", token, params=params)

    async def get_entry(self, entry_id: str, token: str) -> dict:
        return await _request("GET", f"{config.logbook_service_url()}/v1/entries/{entry_id}", token)

    async def progress(self, placement_id: str, token: str) -> dict:
        return await _request("GET", f"{config.logbook_service_url()}/v1/placements/{placement_id}/progress",
                              token)

    async def review(self, entry_id: str, decision: str, comment: str | None, token: str) -> dict:
        return await _request("POST", f"{config.logbook_service_url()}/v1/entries/{entry_id}/reviews",
                              token, json={"decision": decision, "comment": comment})
