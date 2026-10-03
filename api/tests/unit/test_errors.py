import json

from fastapi.responses import JSONResponse

from app.core.context import request_id_var
from app.core.errors import Conflict, ShuttingDown, _Config, problem, render


def _body(response: JSONResponse) -> dict[str, object]:
    return dict(json.loads(bytes(response.body)))


def test_problem_shape_and_media_type() -> None:
    token = request_id_var.set("req_test")
    try:
        response = problem(404, "note_not_found", "Note not found", detail="gone")
    finally:
        request_id_var.reset(token)
    body = _body(response)
    assert response.media_type == "application/problem+json"
    assert body == {
        "type": _Config.errors_base_url + "note_not_found",  # set by the profile
        "title": "Note not found",
        "status": 404,
        "code": "note_not_found",
        "requestId": "req_test",
        "retryable": False,
        "detail": "gone",
    }


def test_retry_after_goes_in_body_and_header() -> None:
    response = render(ShuttingDown(retry_after=5))
    assert response.status_code == 503
    assert response.headers["retry-after"] == "5"
    body = _body(response)
    assert body["retryAfter"] == 5 and body["retryable"] is True


class TitleTaken(Conflict):
    code, title = "title_taken", "Taken"


def test_subclass_error_carries_its_code() -> None:
    body = _body(render(TitleTaken()))
    assert body["status"] == 409 and body["code"] == "title_taken"
