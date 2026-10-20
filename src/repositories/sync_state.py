from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain import SyncState
from src.models import SyncMetadata

STATE_ID = 1


class SyncStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> SyncState:
        row = await self._session.get(SyncMetadata, STATE_ID)
        if row is None:
            return SyncState()
        return SyncState(
            last_sync_time=row.last_sync_time,
            last_changed_at=row.last_changed_at,
            sync_status=row.sync_status,
        )

    async def save(self, state: SyncState) -> None:
        values = {
            "last_sync_time": state.last_sync_time,
            "last_changed_at": state.last_changed_at,
            "sync_status": state.sync_status,
        }
        stmt = insert(SyncMetadata).values(id=STATE_ID, **values)
        stmt = stmt.on_conflict_do_update(index_elements=[SyncMetadata.id], set_=values)
        await self._session.execute(stmt)
        await self._session.commit()
