from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_get_seats_usecase
from src.domain import EventNotFound, EventUnexpectedStatus
from src.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def override_usecase(**kwargs) -> None:
    usecase = MagicMock()
    usecase.do = AsyncMock(**kwargs)
    app.dependency_overrides[get_get_seats_usecase] = lambda: usecase


def test_seats_ok():
    override_usecase(return_value=["A1", "A3"])

    response = client.get("/api/events/e1/seats")

    assert response.status_code == 200
    assert response.json() == {"event_id": "e1", "available_seats": ["A1", "A3"]}


def test_seats_event_not_found():
    override_usecase(side_effect=EventNotFound("e1"))

    assert client.get("/api/events/e1/seats").status_code == 404


def test_seats_event_not_published():
    override_usecase(side_effect=EventUnexpectedStatus("new"))

    assert client.get("/api/events/e1/seats").status_code == 400
