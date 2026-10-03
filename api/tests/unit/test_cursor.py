import uuid
from datetime import UTC, datetime

import pytest

from app.core.errors import InvalidCursor
from app.core.schemas import decode_cursor, encode_cursor


def test_cursor_round_trip() -> None:
    at, row_id = datetime(2026, 9, 30, 12, 0, tzinfo=UTC), uuid.uuid4()
    assert decode_cursor(encode_cursor(at, row_id)) == (at, row_id)


@pytest.mark.parametrize("bad", ["", "nope", "W10", "WyJ4IiwgInkiXQ"])
def test_bad_cursor_is_invalid_request(bad: str) -> None:
    with pytest.raises(InvalidCursor):
        decode_cursor(bad)
