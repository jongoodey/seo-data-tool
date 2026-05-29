from seo_analyser.runner.errors import RunError, normalise


class _FakeApiException(Exception):
    def __init__(self, status, body=""):
        super().__init__(body)
        self.status = status
        self.body = body


def test_auth_error():
    err = normalise(_FakeApiException(401, "unauthorized"))
    assert isinstance(err, RunError)
    assert err.kind == "auth"
    assert err.status_code == 401


def test_rate_limit():
    assert normalise(_FakeApiException(429)).kind == "rate_limit"


def test_bad_request():
    assert normalise(_FakeApiException(404)).kind == "bad_request"


def test_server_error():
    assert normalise(_FakeApiException(500)).kind == "server"


def test_network_error():
    assert normalise(ConnectionError("boom")).kind == "network"
