"""The only place that talks to the placement service (the data owner)."""
import httpx

from app import config
from app.errors import ApiError


class PlacementClient:
    def get(self, placement_id: str, token: str) -> dict:
        try:
            r = httpx.get(f"{config.placement_service_url()}/v1/placements/{placement_id}",
                          headers={"Authorization": f"Bearer {token}"}, timeout=5.0)
        except httpx.HTTPError:
            raise ApiError(503, "placement_service_unavailable", "The placement service cannot be reached")
        if r.status_code == 404:
            raise ApiError(404, "placement_not_found", f"Placement {placement_id} not found")
        if r.status_code != 200:
            raise ApiError(502, "placement_service_error", f"Placement service answered {r.status_code}")
        return r.json()


def get_placement_client() -> PlacementClient:
    return PlacementClient()