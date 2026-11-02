import pandas as pd
import pytest
import requests

from Financial_toolkit.data.providers import TwelveDataProvider


@pytest.fixture
def provider():
    return TwelveDataProvider(api_key="test_api_key")


def test_twelve_data_provider_rejects_empty_tickers(provider):

    with pytest.raises(ValueError):
        provider.download_prices(
            [],
            "2025-01-01",
            "2025-01-31"
        )


def test_twelve_data_provider_accepts_single_ticker(provider, monkeypatch):

    response_data = {
        "meta": {"symbol": "AAPL"},
        "values": [
            {
                "datetime": "2025-01-02",
                "open": "98.0",
                "high": "102.0",
                "low": "97.0",
                "close": "100.0",
                "volume": "1000"
            },
            {
                "datetime": "2025-01-03",
                "open": "99.0",
                "high": "103.0",
                "low": "98.0",
                "close": "101.0",
                "volume": "1200"
            }
        ],
        "status": "ok"
    }

    class FakeResponse:

        def raise_for_status(self):
            pass

        def json(self):
            return response_data

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "Financial_toolkit.data.providers.requests.get",
        fake_get
    )

    result = provider.download_prices(
        ["aapl"],
        "2025-01-01",
        "2025-01-31"
    )

    assert len(result) == 2
    assert result["ticker"].unique().tolist() == ["AAPL"]
    assert result["close"].tolist() == [100.0, 101.0]
    assert result["adj_close"].isna().all()
    assert pd.api.types.is_datetime64_any_dtype(result["date"])


def test_twelve_data_provider_normalizes_multiple_tickers(
    provider,
    monkeypatch
):

    responses = {
        "AAPL": {
            "status": "ok",
            "values": [
                {
                    "datetime": "2025-01-02",
                    "open": "98",
                    "high": "102",
                    "low": "97",
                    "close": "100",
                    "volume": "1000"
                }
            ]
        },
        "MSFT": {
            "status": "ok",
            "values": [
                {
                    "datetime": "2025-01-02",
                    "open": "198",
                    "high": "202",
                    "low": "197",
                    "close": "200",
                    "volume": "2000"
                }
            ]
        }
    }

    def fake_get(*args, **kwargs):
        symbol = kwargs["params"]["symbol"]

        class FakeResponse:

            def raise_for_status(self):
                pass

            def json(self):
                return responses[symbol]

        return FakeResponse()

    monkeypatch.setattr(
        "Financial_toolkit.data.providers.requests.get",
        fake_get
    )

    result = provider.download_prices(
        ["AAPL", "MSFT"],
        "2025-01-01",
        "2025-01-31"
    )

    assert len(result) == 2
    assert set(result["ticker"]) == {"AAPL", "MSFT"}
    assert set(result.columns) == {
        "ticker",
        "date",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume"
    }


def test_twelve_data_provider_rejects_invalid_dates(provider):

    with pytest.raises(ValueError):
        provider.download_prices(
            ["AAPL"],
            "2025-01-31",
            "2025-01-01"
        )


def test_twelve_data_provider_rejects_malformed_dates(provider):

    with pytest.raises(ValueError):
        provider.download_prices(
            ["AAPL"],
            "invalid-date",
            "2025-01-31"
        )


def test_twelve_data_provider_rejects_empty_response(
    provider,
    monkeypatch
):

    class FakeResponse:

        def raise_for_status(self):
            pass

        def json(self):
            return {"status": "ok", "values": []}

    monkeypatch.setattr(
        "Financial_toolkit.data.providers.requests.get",
        lambda *args, **kwargs: FakeResponse()
    )

    with pytest.raises(ValueError):
        provider.download_prices(
            ["AAPL"],
            "2025-01-01",
            "2025-01-31"
        )


def test_twelve_data_provider_handles_api_error(
    provider,
    monkeypatch
):

    class FakeResponse:

        def raise_for_status(self):
            pass

        def json(self):
            return {
                "status": "error",
                "code": 401,
                "message": "Invalid API key"
            }

    monkeypatch.setattr(
        "Financial_toolkit.data.providers.requests.get",
        lambda *args, **kwargs: FakeResponse()
    )

    with pytest.raises(ValueError):
        provider.download_prices(
            ["AAPL"],
            "2025-01-01",
            "2025-01-31"
        )


def test_twelve_data_provider_handles_http_error(
    provider,
    monkeypatch
):

    class FakeResponse:

        def raise_for_status(self):
            raise requests.HTTPError("HTTP error")

    monkeypatch.setattr(
        "Financial_toolkit.data.providers.requests.get",
        lambda *args, **kwargs: FakeResponse()
    )

    with pytest.raises(requests.HTTPError):
        provider.download_prices(
            ["AAPL"],
            "2025-01-01",
            "2025-01-31"
        )


def test_twelve_data_provider_requires_api_key(monkeypatch):

    monkeypatch.delenv("TWELVE_DATA_API_KEY", raising=False)

    with pytest.raises(ValueError):
        TwelveDataProvider()