from src.core.cache import TTLCache


def make_cache(now: list[float]) -> TTLCache[list[str]]:
    return TTLCache[list[str]](ttl_seconds=30, clock=lambda: now[0])


def test_returns_value_before_expiry():
    now = [0.0]
    cache = make_cache(now)
    cache.set("k", ["A1"])

    now[0] = 29.9

    assert cache.get("k") == ["A1"]


def test_value_expires_after_ttl():
    now = [0.0]
    cache = make_cache(now)
    cache.set("k", ["A1"])

    now[0] = 30.0

    assert cache.get("k") is None


def test_delete_removes_value():
    cache = make_cache([0.0])
    cache.set("k", ["A1"])

    cache.delete("k")

    assert cache.get("k") is None
