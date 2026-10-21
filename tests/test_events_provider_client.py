from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.clients.events_provider import EventsProviderClient
from src.domain import RequestRejected


def make_response(data: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = data
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def client() -> EventsProviderClient:
    return EventsProviderClient(base_url="http://provider", api_key="key")


@pytest.mark.anyio
async def test_events_first_page(client):
    data = {
        "next": "http://host/api/events/?changed_at=2000-01-01&cursor=abc",
        "previous": None,
        "results": [{"id": "1"}],
    }
    mock_get = AsyncMock(return_value=make_response(data))
    with patch.object(client._client, "get", mock_get):
        page = await client.events("2000-01-01")

    mock_get.assert_awaited_once_with(
        "/api/events/", params={"changed_at": "2000-01-01"}
    )
    assert page.results == [{"id": "1"}]
    assert page.next_cursor == "abc"


@pytest.mark.anyio
async def test_events_passes_cursor(client):
    data = {"next": None, "previous": "http://host/x", "results": []}
    mock_get = AsyncMock(return_value=make_response(data))
    with patch.object(client._client, "get", mock_get):
        page = await client.events("2000-01-01", cursor="abc")

    mock_get.assert_awaited_once_with(
        "/api/events/", params={"changed_at": "2000-01-01", "cursor": "abc"}
    )
    assert page.next_cursor is None


@pytest.mark.anyio
async def test_events_next_without_cursor_raises(client):
    data = {"next": "http://host/api/events/?changed_at=2000-01-01", "results": []}
    mock_get = AsyncMock(return_value=make_response(data))
    with patch.object(client._client, "get", mock_get):
        with pytest.raises(ValueError):
            await client.events("2000-01-01")


@pytest.mark.anyio
async def test_events_http_error_propagates(client):
    response = make_response({})
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "error", request=MagicMock(), response=MagicMock()
    )
    mock_get = AsyncMock(return_value=response)
    with patch.object(client._client, "get", mock_get):
        with pytest.raises(httpx.HTTPStatusError):
            await client.events("2000-01-01")


@pytest.mark.anyio
async def test_seats(client):
    mock_get = AsyncMock(return_value=make_response({"seats": ["A1", "A3"]}))
    with patch.object(client._client, "get", mock_get):
        seats = await client.seats("e1")

    mock_get.assert_awaited_once_with("/api/events/e1/seats/")
    assert seats == ["A1", "A3"]


@pytest.mark.anyio
async def test_register(client):
    response = make_response({"ticket_id": "t1"})
    response.status_code = 201
    mock_post = AsyncMock(return_value=response)
    with patch.object(client._client, "post", mock_post):
        ticket_id = await client.register(
            "e1", "Ivan", "Ivanov", "ivan@example.com", "A5"
        )

    assert ticket_id == "t1"
    mock_post.assert_awaited_once_with(
        "/api/events/e1/register/",
        json={
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "seat": "A5",
            "email": "ivan@example.com",
        },
    )


@pytest.mark.anyio
async def test_register_rejected_by_provider(client):
    response = make_response({})
    response.status_code = 400
    response.text = '["This ticket is not available (already sold)."]'
    mock_post = AsyncMock(return_value=response)
    with patch.object(client._client, "post", mock_post):
        with pytest.raises(RequestRejected):
            await client.register("e1", "Ivan", "Ivanov", "ivan@example.com", "A5")


@pytest.mark.anyio
async def test_unregister(client):
    response = make_response({"success": True})
    response.status_code = 200
    mock_request = AsyncMock(return_value=response)
    with patch.object(client._client, "request", mock_request):
        await client.unregister("e1", "t1")

    mock_request.assert_awaited_once_with(
        "DELETE", "/api/events/e1/unregister/", json={"ticket_id": "t1"}
    )
