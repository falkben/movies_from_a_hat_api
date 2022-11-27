from collections import namedtuple

import httpx
import pytest
import respx
from fastapi import HTTPException
from loguru import logger

from app.config import Settings
from app.tmdb import formatter, get_movie_data, resp_error_handling

MockRoutes = namedtuple("TestRoute", ["url", "method", "status_code"])

test_routes = {
    "test_get_url_400": MockRoutes(
        "http://testserver/get/bad?query_param=BAD", "GET", 400
    ),
    "test_get_url_500": MockRoutes(
        "http://testserver/get/down?query_param=1234", "GET", 500
    ),
    "test_post_url_400": MockRoutes("http://testserver/post/bad", "POST", 400),
    "test_post_url_500": MockRoutes("http://testserver/post/down", "POST", 500),
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


async def test_get_movie_data(settings: Settings, mocked_TMDB_movie_results):

    movie_data, rating, genres = await get_movie_data(
        115, settings.tmdb_api_url, settings.tmdb_api_key
    )
    assert movie_data.title == "The Big Lebowski"
    assert rating == "R"
    assert genres == ["Comedy", "Crime"]


async def test_get_movie_data_not_found(
    settings: Settings, mocked_TMDB_movie_results, caplog
):

    with pytest.raises(HTTPException):
        await get_movie_data(0, settings.tmdb_api_url, settings.tmdb_api_key)

    assert "404" in caplog.text


@pytest.fixture
def writer():
    def w(message):
        w.written.append(message)

    w.written = []
    w.read = lambda: "".join(w.written)
    w.clear = lambda: w.written.clear()

    return w


async def test_api_key_obfuscated(writer, settings):
    """Set up a logging handler and test our handler

    caplog fixture doesn't use our custom formatter
    """

    logger.add(writer, format=formatter)

    message = "Error from TMDB. Request: <Request('GET', 'https://api.themoviedb.org/3/movie/0?api_key=TESTING&append_to_response=release_dates')>, Response: <Response [404 Not Found]>"
    logger.log(10, message)

    result = writer.read().rstrip("\n")

    assert f"api_key={settings.tmdb_api_key}" not in result
    assert "api_key=xxxxxx" in result
