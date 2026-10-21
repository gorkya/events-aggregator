import pytest

from src.usecases.seat_pattern import seat_in_pattern


@pytest.mark.parametrize(
    ("pattern", "seat", "expected"),
    [
        ("A1-1000,B1-2000", "A1", True),
        ("A1-1000,B1-2000", "A1000", True),
        ("A1-1000,B1-2000", "B2000", True),
        ("A1-1000,B1-2000", "A1001", False),
        ("A1-1000,B1-2000", "C1", False),
        ("A1-1000", "A0", False),
        ("A1-1000", "15", False),
        ("A1-1000", "a15", False),
    ],
)
def test_seat_in_pattern(pattern, seat, expected):
    assert seat_in_pattern(pattern, seat) is expected
