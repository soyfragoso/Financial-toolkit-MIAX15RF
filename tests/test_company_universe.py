import random

import pytest

from Financial_toolkit.data import company_universe as universe


def test_universe_has_five_categories_with_25_companies_each():
    assert set(universe.CATEGORIES) == {"A", "B", "C", "D", "E"}

    for category in universe.CATEGORIES:
        assert len(universe.COMPANY_UNIVERSE[category]) == 25
        assert len(set(universe.COMPANY_UNIVERSE[category])) == 25


def test_category_b_is_artificial_intelligence():
    assert "IA" in universe.CATEGORIES["B"]


def test_generate_proposals_has_five_unique_tickers_per_category():
    proposals = universe.generate_proposals(rng=random.Random(42))

    assert set(proposals) == {"A", "B", "C", "D", "E", "Z"}

    for category in universe.CATEGORIES:
        assert len(proposals[category]) == 5
        assert len(set(proposals[category])) == 5
        assert set(proposals[category]).issubset(
            set(universe.COMPANY_UNIVERSE[category])
        )


def test_diversified_proposal_contains_one_ticker_per_category():
    proposals = universe.generate_proposals(rng=random.Random(42))

    assert len(proposals["Z"]) == 5

    for ticker, category in zip(proposals["Z"], universe.CATEGORIES):
        assert ticker in universe.COMPANY_UNIVERSE[category]


def test_diversified_proposal_has_no_duplicate_tickers_across_categories():
    proposals = universe.generate_proposals(rng=random.Random(42))
    assert len(proposals["Z"]) == len(set(proposals["Z"])) == 5


def test_diversified_proposal_rejects_universe_without_enough_unique_tickers():
    overlapping = {
        category: ["SAME"] * 5
        for category in universe.CATEGORIES
    }

    with pytest.raises(ValueError, match="propuesta diversificada"):
        universe.generate_proposals(overlapping, rng=random.Random(1))


def test_generate_proposals_rejects_categories_with_fewer_than_five():
    incomplete = {
        category: list(tickers)
        for category, tickers in universe.COMPANY_UNIVERSE.items()
    }
    incomplete["C"] = incomplete["C"][:4]

    with pytest.raises(ValueError, match="Energía"):
        universe.generate_proposals(incomplete)


def test_generate_proposals_is_reproducible():
    first = universe.generate_proposals(rng=random.Random(123))
    second = universe.generate_proposals(rng=random.Random(123))

    assert first == second
