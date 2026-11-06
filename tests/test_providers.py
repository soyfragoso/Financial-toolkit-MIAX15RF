import pytest
import requests

from Financial_toolkit.data.providers import (
    DataProvider,
    TwelveDataProvider,
)


def test_data_provider_is_abstract():
    with pytest.raises(TypeError):
        DataProvider()


def test_data_provider_requires_download_prices():

    class IncompleteProvider(DataProvider):
        pass

    with pytest.raises(TypeError):
        IncompleteProvider()


def test_data_provider_accepts_implemented_method():

    class MockProvider(DataProvider):

        def download_prices(self, tickers, start, end):
            return None

    provider = MockProvider()

    assert isinstance(provider, DataProvider)
    assert callable(provider.download_prices)


def test_twelve_data_http_error_does_not_expose_api_key(monkeypatch):
    secret_key = "FAKE_TEST_SECRET_12345"

    response = requests.Response()
    response.status_code = 404
    response.url = (
        "https://api.twelvedata.com/time_series"
        f"?symbol=7267.T&apikey={secret_key}"
    )

    def fake_get(*args, **kwargs):
        return response

    monkeypatch.setattr(
        "Financial_toolkit.data.providers.requests.get",
        fake_get,
    )

    provider = TwelveDataProvider(api_key=secret_key)

    with pytest.raises(requests.HTTPError) as captured:
        provider.download_prices(
            tickers=["7267.T"],
            start="2025-01-01",
            end="2025-02-01",
        )

    error_text = str(captured.value)
    error_repr = repr(captured.value)

    assert "7267.T" in error_text
    assert "HTTP 404" in error_text
    assert secret_key not in error_text
    assert secret_key not in error_repr
    assert "apikey=" not in error_text
