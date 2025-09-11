import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from radiobridge.providers.rb_api import RepeaterBookAPIProvider
from radiobridge.lightweight_data import LightDataFrame
from radiobridge.errors import HTTPRequestError, ParseError


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, headers=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.headers = headers or {"content-type": "application/json"}
        self.text = text

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data


def test_api_provider_happy_path(monkeypatch):
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append((url, params, headers, timeout))
        data = [{"frequency": "146.520", "callsign": "W6ABC"}]
        return DummyResponse(200, json_data=data)

    sess = Mock()
    sess.get = fake_get
    p = RepeaterBookAPIProvider(session=sess, retries=0)
    df = p.fetch({"country": "United States", "state": "CA", "band": "2m"})
    assert isinstance(df, LightDataFrame)
    assert len(df) == 1
    assert "frequency" in df.columns


def test_api_provider_429_retry_then_success(monkeypatch):
    seq = [
        DummyResponse(429, json_data=[{}], headers={"Retry-After": "0.0"}),
        DummyResponse(200, json_data=[{"frequency": "147.000"}]),
    ]

    def fake_get(url, params=None, headers=None, timeout=None):
        return seq.pop(0)

    sess = Mock()
    sess.get = fake_get
    p = RepeaterBookAPIProvider(session=sess, retries=1, retry_backoff=0.0, rate_jitter=0.0)
    df = p.fetch({"country": "United States", "state": "CA"})
    assert len(df) == 1


def test_api_provider_parse_error(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        # Return non-JSON
        resp = DummyResponse(200, json_data=ValueError("bad json"))
        resp.headers = {"content-type": "text/plain"}
        return resp

    sess = Mock()
    sess.get = fake_get
    p = RepeaterBookAPIProvider(session=sess, retries=0)
    with pytest.raises(ParseError):
        p.fetch({"country": "United States", "state": "CA"})


def test_api_provider_5xx_exhaust(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return DummyResponse(503, json_data=[{}])

    sess = Mock()
    sess.get = fake_get
    p = RepeaterBookAPIProvider(session=sess, retries=1, retry_backoff=0.0, rate_jitter=0.0)
    with pytest.raises(HTTPRequestError):
        p.fetch({"country": "United States", "state": "CA"})
