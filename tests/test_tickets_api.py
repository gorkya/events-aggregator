from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_cancel_ticket_usecase, get_create_ticket_usecase
from src.domain import EventNotFound, RegistrationClosed, TicketNotFound
from src.main import app

client = TestClient(app)

VALID_BODY = {
    "event_id": "e1",
    "first_name": "Ivan",
    "last_name": "Ivanov",
    "email": "ivan@example.com",
    "seat": "A15",
}


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def override(dependency, **kwargs) -> None:
    usecase = MagicMock()
    usecase.do = AsyncMock(**kwargs)
    app.dependency_overrides[dependency] = lambda: usecase


def test_create_ticket_returns_201():
    override(get_create_ticket_usecase, return_value="t1")

    response = client.post("/api/tickets", json=VALID_BODY)

    assert response.status_code == 201
    assert response.json() == {"ticket_id": "t1"}


def test_create_ticket_invalid_email_returns_422():
    override(get_create_ticket_usecase, return_value="t1")

    response = client.post("/api/tickets", json={**VALID_BODY, "email": "nope"})

    assert response.status_code == 422


def test_create_ticket_invalid_seat_format_returns_422():
    override(get_create_ticket_usecase, return_value="t1")

    response = client.post("/api/tickets", json={**VALID_BODY, "seat": "15"})

    assert response.status_code == 422


def test_create_ticket_event_not_found_returns_404():
    override(get_create_ticket_usecase, side_effect=EventNotFound("e1"))

    response = client.post("/api/tickets", json=VALID_BODY)

    assert response.status_code == 404


def test_create_ticket_business_error_returns_400():
    override(
        get_create_ticket_usecase,
        side_effect=RegistrationClosed("Registration deadline has passed"),
    )

    response = client.post("/api/tickets", json=VALID_BODY)

    assert response.status_code == 400
    assert response.json()["detail"] == "Registration deadline has passed"


def test_cancel_ticket_returns_success():
    override(get_cancel_ticket_usecase, return_value=None)

    response = client.delete("/api/tickets/t1")

    assert response.status_code == 200
    assert response.json() == {"success": True}


def test_cancel_ticket_not_found_returns_404():
    override(get_cancel_ticket_usecase, side_effect=TicketNotFound("t1"))

    assert client.delete("/api/tickets/t1").status_code == 404
