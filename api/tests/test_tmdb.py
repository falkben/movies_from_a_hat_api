from collections import namedtuple

import httpx
import pytest
import respx
from fastapi import HTTPException

from app.tmdb import resp_error_handling

TestRoute = namedtuple("TestRoute", ["url", "method", "status_code"])

test_routes = {
    "test_get_url_400": TestRoute(
        "http://testserver/get/bad?query_param=BAD", "GET", 400
    ),
    "test_get_url_500": TestRoute(
        "http://testserver/get/down?query_param=1234", "GET", 500
    ),
    "test_post_url_400": TestRoute("http://testserver/post/bad", "POST", 400),
    "test_post_url_500": TestRoute("http://testserver/post/down", "POST", 500),
}


@pytest.fixture
def mock_urls():

    with respx.mock(assert_all_called=False) as respx_mock:

        for url, method, status_code in test_routes.values():
            route = respx_mock.request(method, url)
            route.return_value = httpx.Response(status_code)

        yield respx_mock


@pytest.mark.parametrize("test_route", test_routes.values())
def test_error_handling_tmdb(test_route, mock_urls, caplog):

    test_url, method, status_code = test_route

    kwargs = {}
    if method == "POST":
        kwargs["json"] = {"key": "value"}

    resp = httpx.request(method, test_url, **kwargs)
    with pytest.raises(HTTPException) as exc_info:
        resp_error_handling(resp)
    if 400 <= status_code < 500:
        expected_status_code = 400
    else:
        expected_status_code = 504
    assert exc_info.value.status_code == expected_status_code

    assert "Error from TMDB" in caplog.text, caplog.text
    assert test_url in caplog.text, caplog.text
    assert str(status_code) in caplog.text
