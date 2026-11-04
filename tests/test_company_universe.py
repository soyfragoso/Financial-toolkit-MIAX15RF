import random
from datetime import date, timedelta

import pandas as pd
import pytest

from Financial_toolkit.data import company_universe as universe


def make_rankings():
    return {
        category: [
            (f"{category}{number}", 0.10 * number)
            for number in range(1, 9)
        ]
        for category in universe.CATEGORIES
    }


def test_rank_companies_rejects_invalid_parameters():
    with pytest.raises(ValueError):
        universe.rank_companies(years=0)

    with pytest.raises(ValueError):
        universe.rank_companies(limit=0)


def test_generate_proposals_has_five_unique_tickers_per_category():
    rankings = make_rankings()

    proposals = universe.generate_proposals(
        rankings,
        rng=random.Random(42),
    )

    assert set(proposals) == {"A", "B", "C", "D", "E", "Z"}

    for category in universe.CATEGORIES:
        assert len(proposals[category]) == 5
        assert len(set(proposals[category])) == 5

        available = {ticker for ticker, _ in rankings[category]}
        assert set(proposals[category]).issubset(available)


def test_diversified_proposal_contains_one_ticker_per_category():
    rankings = make_rankings()

    proposals = universe.generate_proposals(
        rankings,
        rng=random.Random(42),
    )

    assert len(proposals["Z"]) == 5

    for ticker, category in zip(
        proposals["Z"],
        universe.CATEGORIES,
    ):
        available = {item[0] for item in rankings[category]}
        assert ticker in available


def test_generate_proposals_rejects_categories_with_fewer_than_five():
    rankings = make_rankings()
    rankings["C"] = rankings["C"][:4]

    with pytest.raises(ValueError, match="Energía"):
        universe.generate_proposals(rankings)


def test_rank_companies_orders_returns_and_excludes_short_history(
    monkeypatch,
):
    today = date.today()
    monkeypatch.setattr(
        universe,
        "COMPANY_UNIVERSE",
        {"A": ["AAA", "BBB", "BAD"]},
    )

    class FakeProvider:
        def download_prices(self, tickers, start, end):
            start_date = date.fromisoformat(start)
            end_date = date.fromisoformat(end) - timedelta(days=1)

            middle_date = start_date + (
                end_date - start_date
            ) // 2

            prices = {
                "AAA": [10.0, 15.0, 20.0],
                "BBB": [10.0, 20.0, 40.0],
                "BAD": [10.0, 20.0, 50.0],
            }

            rows = []

            for ticker in tickers:
                dates = [
                    start_date,
                    middle_date,
                    end_date,
                ]

                if ticker == "BAD":
                    dates[0] = start_date + timedelta(days=120)

                for current_date, price in zip(
                    dates,
                    prices[ticker],
                ):
                    rows.append({
                        "ticker": ticker,
                        "date": current_date,
                        "adj_close": price,
                        "close": price,
                    })

            return pd.DataFrame(rows)

    result = universe.rank_companies(
        provider=FakeProvider(),
        years=5,
        limit=1,
    )

    assert list(result) == ["A"]
    assert result["A"] == [("BBB", pytest.approx(3.0))]


def test_generate_proposals_is_reproducible():
    rankings = make_rankings()

    first = universe.generate_proposals(
        rankings,
        rng=random.Random(123),
    )
    second = universe.generate_proposals(
        rankings,
        rng=random.Random(123),
    )

    assert first == second
