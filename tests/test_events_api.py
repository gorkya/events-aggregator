from unittest.mock import AsyncMock, MagicMock
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_get_event_usecase, get_list_events_usecase
from src.domain import EventNotFound
from src.main import app
from src.usecases.get_events import EventsList
from tests.factories import make_event

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def override_list(count: int) -> None:
    usecase = MagicMock()
    usecase.do = AsyncMock(return_value=EventsList(count=count, items=[make_event()]))
    app.dependency_overrides[get_list_events_usecase] = lambda: usecase


def test_list_events_middle_page_has_next_and_previous():
    override_list(count=45)

    response = client.get("/api/events?page=2&page_size=20&date_from=2026-01-01")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 45
    assert len(body["results"]) == 1
    next_query = parse_qs(urlparse(body["next"]).query)
    assert next_query["page"] == ["3"]
    assert next_query["date_from"] == ["2026-01-01"]
    assert parse_qs(urlparse(body["previous"]).query)["page"] == ["1"]


def test_list_events_last_page_has_no_next():
    override_list(count=45)

    body = client.get("/api/events?page=3&page_size=20").json()

    assert body["next"] is None
    assert body["previous"] is not None


def test_list_events_rejects_invalid_page():
    response = client.get("/api/events?page=0")

    assert response.status_code == 400


def test_get_event_not_found_returns_404():
    usecase = MagicMock()
    usecase.do = AsyncMock(side_effect=EventNotFound("missing"))
    app.dependency_overrides[get_get_event_usecase] = lambda: usecase

    response = client.get("/api/events/missing")

    assert response.status_code == 404


def test_get_event_returns_details_with_seats_pattern():
    usecase = MagicMock()
    usecase.do = AsyncMock(return_value=make_event("e1"))
    app.dependency_overrides[get_get_event_usecase] = lambda: usecase

    response = client.get("/api/events/e1")

    assert response.status_code == 200
    assert response.json()["place"]["seats_pattern"] == "A1-10"
