from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain import SyncState
from src.usecases.sync_events import SyncEventsUsecase


def make_raw_event(event_id: str, changed_at: str) -> dict:
    return {
        "id": event_id,
        "name": "Event",
        "place": {
            "id": "place-1",
            "name": "Place",
            "city": "City",
            "address": "Address",
            "seats_pattern": "A1-10",
            "changed_at": "2025-01-01T03:00:00+03:00",
        },
        "event_time": "2026-01-11T17:00:00+03:00",
        "registration_deadline": "2026-01-10T17:00:00+03:00",
        "status": "published",
        "number_of_visitors": 0,
        "changed_at": changed_at,
    }


def make_source(raw_events: list[dict], calls: list[str]):
    async def source(changed_at: str):
        calls.append(changed_at)
        for raw in raw_events:
            yield raw

    return source


def make_repos(state: SyncState | None = None):
    events_repo = MagicMock()
    events_repo.upsert_many = AsyncMock()
    state_repo = MagicMock()
    state_repo.get = AsyncMock(return_value=state or SyncState())
    state_repo.save = AsyncMock()
    return events_repo, state_repo


@pytest.mark.anyio
async def test_first_sync_uses_default_date_and_saves_max_changed_at():
    calls: list[str] = []
    source = make_source(
        [
            make_raw_event("1", "2026-01-04T10:00:00+03:00"),
            make_raw_event("2", "2026-01-05T15:30:00+03:00"),
        ],
        calls,
    )
    events_repo, state_repo = make_repos()

    await SyncEventsUsecase(source, events_repo, state_repo).do()

    assert calls == ["2000-01-01"]
    events_repo.upsert_many.assert_awaited_once()
    saved = events_repo.upsert_many.await_args.args[0]
    assert [event.id for event in saved] == ["1", "2"]

    final_state = state_repo.save.await_args_list[-1].args[0]
    assert final_state.sync_status == "success"
    assert final_state.last_sync_time is not None
    assert final_state.last_changed_at == datetime.fromisoformat(
        "2026-01-05T15:30:00+03:00"
    )


@pytest.mark.anyio
async def test_incremental_sync_uses_date_of_last_changed_at():
    last_changed_at = datetime.fromisoformat("2026-01-05T15:30:00+03:00")
    calls: list[str] = []
    events_repo, state_repo = make_repos(
        SyncState(last_changed_at=last_changed_at, sync_status="success")
    )

    await SyncEventsUsecase(make_source([], calls), events_repo, state_repo).do()

    assert calls == ["2026-01-05"]
    events_repo.upsert_many.assert_not_awaited()
    final_state = state_repo.save.await_args_list[-1].args[0]
    assert final_state.last_changed_at == last_changed_at


@pytest.mark.anyio
async def test_failed_sync_keeps_last_changed_at():
    async def failing_source(changed_at: str):
        yield make_raw_event("1", "2026-01-04T10:00:00+03:00")
        raise RuntimeError("boom")

    events_repo, state_repo = make_repos()

    with pytest.raises(RuntimeError):
        await SyncEventsUsecase(failing_source, events_repo, state_repo).do()

    events_repo.upsert_many.assert_not_awaited()
    final_state = state_repo.save.await_args_list[-1].args[0]
    assert final_state.sync_status == "failed"
    assert final_state.last_changed_at is None
