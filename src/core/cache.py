import time
from collections.abc import Callable


class TTLCache[T]:
    def __init__(
        self,
        ttl_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_seconds
        self._clock = clock
        self._items: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> T | None:
        item = self._items.get(key)
        if item is None:
            return None
        expires_at, value = item
        if self._clock() >= expires_at:
            del self._items[key]
            return None
        return value

    def set(self, key: str, value: T) -> None:
        self._items[key] = (self._clock() + self._ttl, value)

    def delete(self, key: str) -> None:
        self._items.pop(key, None)
