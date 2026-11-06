import pandas as pd
import pytest
from unittest.mock import Mock

from Financial_toolkit.data.providers import (
    YahooFinanceProvider,
    TwelveDataProvider,
)


INDEX_TICKERS = [
    "^GSPC",       # S&P 500
    "^IBEX",       # IBEX 35
    "^STOXX50E",   # EURO STOXX 50
]

STANDARD_COLUMNS = [
    "ticker",
    "date",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
]


def test_yahoo_finance_normalizes_three_stock_indices(monkeypatch):
    fields = [
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
        "Volume",
    ]

    columns = pd.MultiIndex.from_product(
        [INDEX_TICKERS, fields]
    )

    data = [
        [
            100.0, 105.0, 99.0, 103.0, 103.0, 1000,
            200.0, 205.0, 199.0, 203.0, 203.0, 2000,
            300.0, 305.0, 299.0, 303.0, 303.0, 3000,
        ],
        [
            101.0, 106.0, 100.0, 104.0, 104.0, 1100,
            201.0, 206.0, 200.0, 204.0, 204.0, 2100,
            301.0, 306.0, 300.0, 304.0, 304.0, 3100,
        ],
    ]

    raw_data = pd.DataFrame(
        data,
        columns=columns,
        index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
    )

    mocked_download = Mock(return_value=raw_data)

    monkeypatch.setattr(
        "Financial_toolkit.data.providers.yf.download",
        mocked_download,
    )

    provider = YahooFinanceProvider()
    result = provider.download_prices(
        INDEX_TICKERS,
        "2024-01-01",
        "2024-01-05",
    )

    assert list(result.columns) == STANDARD_COLUMNS
    assert set(result["ticker"]) == set(INDEX_TICKERS)
    assert len(result) == 6
    assert result.groupby("ticker").size().to_dict() == {
        ticker: 2 for ticker in INDEX_TICKERS
    }

    mocked_download.assert_called_once()
    assert mocked_download.call_args.kwargs["tickers"] == INDEX_TICKERS


@pytest.mark.parametrize("ticker", INDEX_TICKERS)
def test_twelve_data_requests_stock_index_and_normalizes_response(
    monkeypatch,
    ticker,
):
    payload = {
        "values": [
            {
                "datetime": "2024-01-03",
                "open": "101",
                "high": "106",
                "low": "100",
                "close": "104",
                "volume": "1100",
            },
            {
                "datetime": "2024-01-02",
                "open": "100",
                "high": "105",
                "low": "99",
                "close": "103",
                "volume": "1000",
            },
        ]
    }

    mocked_get = Mock()
    mocked_response = Mock()
    mocked_response.json.return_value = payload
    mocked_response.raise_for_status.return_value = None
    mocked_get.return_value = mocked_response

    monkeypatch.setattr(
        "Financial_toolkit.data.providers.requests.get",
        mocked_get,
    )

    provider = TwelveDataProvider(api_key="test-key")
    result = provider.download_prices(
        [ticker],
        "2024-01-01",
        "2024-01-05",
    )

    assert list(result.columns) == STANDARD_COLUMNS
    assert set(result["ticker"]) == {ticker}
    assert len(result) == 2
    assert result["date"].is_monotonic_increasing
    assert result["close"].tolist() == [103.0, 104.0]

    requested_params = mocked_get.call_args.kwargs["params"]
    assert requested_params["symbol"] == ticker


def test_yahoo_finance_keeps_indices_in_standard_format(monkeypatch):
    fields = [
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
        "Volume",
    ]
    columns = pd.MultiIndex.from_product(
        [INDEX_TICKERS, fields]
    )
    raw_data = pd.DataFrame(
        [[100, 105, 99, 103, 103, 1000] * 3],
        columns=columns,
        index=pd.to_datetime(["2024-01-02"]),
    )

    monkeypatch.setattr(
        "Financial_toolkit.data.providers.yf.download",
        Mock(return_value=raw_data),
    )

    result = YahooFinanceProvider().download_prices(
        INDEX_TICKERS,
        "2024-01-01",
        "2024-01-05",
    )

    assert result["ticker"].nunique() == 3
    assert pd.api.types.is_datetime64_any_dtype(result["date"])
    assert pd.api.types.is_numeric_dtype(result["close"])
