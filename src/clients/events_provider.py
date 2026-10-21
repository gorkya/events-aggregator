from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

from src.domain import RequestRejected


@dataclass
class EventsPage:
    results: list[dict[str, Any]]
    next_cursor: str | None


def _extract_cursor(next_url: str | None) -> str | None:
    if not next_url:
        return None
    values = parse_qs(urlparse(next_url).query).get("cursor")
    if not values:
        raise ValueError(f"No cursor in next url: {next_url}")
    return values[0]


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code == 400:
        raise RequestRejected(response.text)
    response.raise_for_status()


class EventsProviderClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"x-api-key": api_key},
            timeout=timeout,
            follow_redirects=True,
        )

    async def events(self, changed_at: str, cursor: str | None = None) -> EventsPage:
        params = {"changed_at": changed_at}
        if cursor:
            params["cursor"] = cursor
        response = await self._client.get("/api/events/", params=params)
        response.raise_for_status()
        data = response.json()
        return EventsPage(
            results=data["results"],
            next_cursor=_extract_cursor(data["next"]),
        )

    async def seats(self, event_id: str) -> list[str]:
        response = await self._client.get(f"/api/events/{event_id}/seats/")
        response.raise_for_status()
        return response.json()["seats"]

    async def register(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> str:
        response = await self._client.post(
            f"/api/events/{event_id}/register/",
            json={
                "first_name": first_name,
                "last_name": last_name,
                "seat": seat,
                "email": email,
            },
        )
        _raise_for_status(response)
        return response.json()["ticket_id"]

    async def unregister(self, event_id: str, ticket_id: str) -> None:
        response = await self._client.request(
            "DELETE",
            f"/api/events/{event_id}/unregister/",
            json={"ticket_id": ticket_id},
        )
        _raise_for_status(response)

    async def aclose(self) -> None:
        await self._client.aclose()
