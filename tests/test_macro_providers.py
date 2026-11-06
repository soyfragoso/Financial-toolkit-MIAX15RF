from unittest.mock import Mock

import pandas as pd
import pytest
import requests

from Financial_toolkit.data.macro_providers import (
    FredDataProvider,
    MacroDataProvider,
)
from Financial_toolkit.models.macro_series import MacroSeries


def make_response(payload):
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_fred_provider_implements_macro_interface():
    provider = FredDataProvider(api_key="test-key")

    assert isinstance(provider, MacroDataProvider)


def test_fred_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    with pytest.raises(ValueError, match="FRED_API_KEY"):
        FredDataProvider()


def test_fred_provider_reads_api_key_from_environment(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "environment-key")

    provider = FredDataProvider()

    assert provider.api_key == "environment-key"


@pytest.mark.parametrize("timeout", [0, -1, 1.5, "30"])
def test_fred_provider_rejects_invalid_timeout(timeout):
    with pytest.raises(ValueError, match="tiempo de espera"):
        FredDataProvider(api_key="test-key", timeout=timeout)


def test_fred_provider_downloads_one_series(monkeypatch):
    payload = {
        "observations": [
            {"date": "2024-01-01", "value": "5.33"},
            {"date": "2024-02-01", "value": "5.33"},
            {"date": "2024-03-01", "value": "5.33"},
        ]
    }
    mocked_get = Mock(return_value=make_response(payload))
    monkeypatch.setattr(
        "Financial_toolkit.data.macro_providers.requests.get",
        mocked_get,
    )

    provider = FredDataProvider(api_key="test-key")
    result = provider.download_series(
        "FEDFUNDS",
        "2024-01-01",
        "2024-03-31",
    )

    assert list(result) == ["FEDFUNDS"]
    assert isinstance(result["FEDFUNDS"], MacroSeries)
    assert len(result["FEDFUNDS"].values) == 3
    assert result["FEDFUNDS"].mean == pytest.approx(5.33)

    kwargs = mocked_get.call_args.kwargs
    assert kwargs["params"]["series_id"] == "FEDFUNDS"
    assert kwargs["params"]["observation_start"] == "2024-01-01"
    assert kwargs["params"]["observation_end"] == "2024-03-31"
    assert kwargs["params"]["api_key"] == "test-key"


def test_fred_provider_downloads_multiple_series(monkeypatch):
    payloads = {
        "FEDFUNDS": {
            "observations": [
                {"date": "2024-01-01", "value": "5.33"},
            ]
        },
        "CPIAUCSL": {
            "observations": [
                {"date": "2024-01-01", "value": "308.4"},
            ]
        },
    }

    def fake_get(url, params, timeout):
        return make_response(payloads[params["series_id"]])

    monkeypatch.setattr(
        "Financial_toolkit.data.macro_providers.requests.get",
        fake_get,
    )

    provider = FredDataProvider(api_key="test-key")
    result = provider.download_series(
        ["FEDFUNDS", "CPIAUCSL"],
        "2024-01-01",
        "2024-12-31",
    )

    assert set(result) == {"FEDFUNDS", "CPIAUCSL"}
    assert result["FEDFUNDS"].values.iloc[0] == pytest.approx(5.33)
    assert result["CPIAUCSL"].values.iloc[0] == pytest.approx(308.4)


def test_fred_provider_normalizes_and_deduplicates_ids(monkeypatch):
    mocked_get = Mock(return_value=make_response({
        "observations": [
            {"date": "2024-01-01", "value": "5.0"},
        ]
    }))
    monkeypatch.setattr(
        "Financial_toolkit.data.macro_providers.requests.get",
        mocked_get,
    )

    provider = FredDataProvider(api_key="test-key")
    result = provider.download_series(
        [" fedfunds ", "FEDFUNDS"],
        "2024-01-01",
        "2024-02-01",
    )

    assert list(result) == ["FEDFUNDS"]
    assert mocked_get.call_count == 1


def test_fred_provider_discards_missing_observations(monkeypatch):
    payload = {
        "observations": [
            {"date": "2024-01-01", "value": "5.33"},
            {"date": "2024-02-01", "value": "."},
            {"date": "2024-03-01", "value": "5.33"},
        ]
    }
    monkeypatch.setattr(
        "Financial_toolkit.data.macro_providers.requests.get",
        Mock(return_value=make_response(payload)),
    )

    provider = FredDataProvider(api_key="test-key")
    result = provider.download_series(
        ["FEDFUNDS"],
        "2024-01-01",
        "2024-03-31",
    )

    values = result["FEDFUNDS"].values

    assert len(values) == 2
    assert pd.Timestamp("2024-02-01") not in values.index


def test_fred_provider_rejects_empty_observations(monkeypatch):
    monkeypatch.setattr(
        "Financial_toolkit.data.macro_providers.requests.get",
        Mock(return_value=make_response({"observations": []})),
    )

    provider = FredDataProvider(api_key="test-key")

    with pytest.raises(ValueError, match="observaciones válidas"):
        provider.download_series(
            ["FEDFUNDS"],
            "2024-01-01",
            "2024-03-31",
        )


def test_fred_provider_rejects_invalid_payload(monkeypatch):
    monkeypatch.setattr(
        "Financial_toolkit.data.macro_providers.requests.get",
        Mock(return_value=make_response(["invalid"])),
    )

    provider = FredDataProvider(api_key="test-key")

    with pytest.raises(ValueError, match="Respuesta no válida"):
        provider.download_series(
            ["FEDFUNDS"],
            "2024-01-01",
            "2024-03-31",
        )


def test_fred_provider_handles_api_error(monkeypatch):
    payload = {
        "error_code": 400,
        "error_message": "Bad Request",
    }
    monkeypatch.setattr(
        "Financial_toolkit.data.macro_providers.requests.get",
        Mock(return_value=make_response(payload)),
    )

    provider = FredDataProvider(api_key="test-key")

    with pytest.raises(ValueError, match="Bad Request"):
        provider.download_series(
            ["INVALID"],
            "2024-01-01",
            "2024-03-31",
        )


def test_fred_provider_propagates_http_errors(monkeypatch):
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("HTTP 500")
    monkeypatch.setattr(
        "Financial_toolkit.data.macro_providers.requests.get",
        Mock(return_value=response),
    )

    provider = FredDataProvider(api_key="test-key")

    with pytest.raises(requests.HTTPError):
        provider.download_series(
            ["FEDFUNDS"],
            "2024-01-01",
            "2024-03-31",
        )


@pytest.mark.parametrize(
    ("series_ids", "start", "end"),
    [
        ([], "2024-01-01", "2024-02-01"),
        ([""], "2024-01-01", "2024-02-01"),
        ([1], "2024-01-01", "2024-02-01"),
        (["FEDFUNDS"], "01-01-2024", "2024-02-01"),
        (["FEDFUNDS"], "2024-02-01", "2024-01-01"),
        (["FEDFUNDS"], "2024-01-01", "2024-01-01"),
    ],
)
def test_fred_provider_rejects_invalid_arguments(
    series_ids,
    start,
    end,
):
    provider = FredDataProvider(api_key="test-key")

    with pytest.raises(ValueError):
        provider.download_series(series_ids, start, end)


def test_fred_provider_rejects_invalid_observation(monkeypatch):
    payload = {
        "observations": [
            {"date": "invalid-date", "value": "5.33"},
        ]
    }
    monkeypatch.setattr(
        "Financial_toolkit.data.macro_providers.requests.get",
        Mock(return_value=make_response(payload)),
    )

    provider = FredDataProvider(api_key="test-key")

    with pytest.raises(ValueError, match="fecha o valor no válido"):
        provider.download_series(
            ["FEDFUNDS"],
            "2024-01-01",
            "2024-03-31",
        )



def test_fred_provider_http_error_does_not_expose_api_key(monkeypatch):
    secret_key = "fakefredsecret1234567890123456"

    response = requests.Response()
    response.status_code = 500
    response.url = (
        "https://api.stlouisfed.org/fred/series/observations"
        f"?series_id=FEDFUNDS&api_key={secret_key}"
    )

    monkeypatch.setattr(
        "Financial_toolkit.data.macro_providers.requests.get",
        Mock(return_value=response),
    )

    provider = FredDataProvider(api_key=secret_key)

    with pytest.raises(requests.HTTPError) as captured:
        provider.download_series(
            ["FEDFUNDS"],
            "2024-01-01",
            "2024-03-31",
        )

    error_text = str(captured.value)
    assert "FEDFUNDS" in error_text
    assert "HTTP 500" in error_text
    assert secret_key not in error_text
    assert secret_key not in repr(captured.value)
    assert "api_key=" not in error_text


def test_fred_provider_api_error_does_not_expose_api_key(monkeypatch):
    secret_key = "fakefredsecret1234567890123456"

    payload = {
        "error_code": 400,
        "error_message": f"Invalid API key: {secret_key}",
    }

    monkeypatch.setattr(
        "Financial_toolkit.data.macro_providers.requests.get",
        Mock(return_value=make_response(payload)),
    )

    provider = FredDataProvider(api_key=secret_key)

    with pytest.raises(ValueError) as captured:
        provider.download_series(
            ["FEDFUNDS"],
            "2024-01-01",
            "2024-03-31",
        )

    error_text = str(captured.value)
    assert secret_key not in error_text
    assert "[CLAVE OCULTA]" in error_text
