import re

_RANGE = re.compile(r"^([A-Z])(\d+)-(\d+)$")
_SEAT = re.compile(r"^([A-Z])(\d+)$")


def seat_in_pattern(pattern: str, seat: str) -> bool:
    seat_match = _SEAT.match(seat)
    if seat_match is None:
        return False
    section, number = seat_match.group(1), int(seat_match.group(2))
    for part in pattern.split(","):
        range_match = _RANGE.match(part.strip())
        if range_match is None:
            continue
        start, end = int(range_match.group(2)), int(range_match.group(3))
        if range_match.group(1) == section and start <= number <= end:
            return True
    return False
