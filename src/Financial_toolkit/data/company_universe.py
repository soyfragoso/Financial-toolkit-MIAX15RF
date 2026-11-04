"""Universos de compañías y selección aleatoria para MIAX 15."""

from __future__ import annotations

import random
from datetime import date, timedelta

import pandas as pd

from Financial_toolkit.data.providers import YahooFinanceProvider


CATEGORIES = {
    "A": "Tecnología",
    "B": "ESG",
    "C": "Energía",
    "D": "Automotrices",
    "E": "Compañías españolas",
}

COMPANY_UNIVERSE = {
    "A": [
        "AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "AMD", "QCOM",
        "TXN", "AMAT", "LRCX", "KLAC", "MU", "ADI", "INTU",
        "NOW", "CRM", "ADBE", "PANW", "CRWD", "ANET", "PLTR",
        "IBM", "CSCO", "ACN", "SHOP", "SNPS", "CDNS", "ASML",
        "TSM", "SAP", "META", "GOOGL", "AMZN", "NFLX", "DELL",
    ],
    "B": [
        "LIN", "WM", "RSG", "ECL", "APD", "NEE", "V", "MA",
        "MSCI", "SPGI", "ICE", "COST", "ORCL", "MSFT", "ADBE",
        "SU.PA", "SIE.DE", "IFX.DE", "NOVO-B.CO", "NVO",
        "ULVR.L", "REL.L", "AZN.L", "DHR", "TMO", "EQIX",
        "AMT", "CCI", "ENPH", "FSLR", "IBE.MC", "SAN.MC",
        "AIR.PA", "DSM.AS", "KER.PA",
    ],
    "C": [
        "XOM", "CVX", "COP", "EOG", "OXY", "SLB", "BKR",
        "HAL", "FANG", "DVN", "APA", "EPD", "ET", "WMB",
        "KMI", "LNG", "EQT", "CTRA", "NEE", "CEG", "VST",
        "FSLR", "ENPH", "BEP", "CNQ", "SU", "BP", "SHEL",
        "TTE", "EQNR", "REP.MC", "IBE.MC", "MPC", "PSX",
        "VLO",
    ],
    "D": [
        "TSLA", "TM", "HMC", "F", "GM", "STLA", "RACE",
        "MBG.DE", "BMW.DE", "VOW3.DE", "7201.T", "7267.T",
        "7203.T", "7269.T", "7270.T", "005380.KS",
        "000270.KS", "012330.KS", "601238.SS", "000625.SZ",
        "1211.HK", "LI", "NIO", "XPEV", "RIVN", "LCID",
        "9868.HK", "9866.HK", "0175.HK", "9863.HK",
        "NKLA", "PSNY", "MBLY", "APTV", "BWA",
    ],
    "E": [
        "IBE.MC", "ITX.MC", "SAN.MC", "BBVA.MC", "CABK.MC",
        "FER.MC", "ACS.MC", "AENA.MC", "ELE.MC", "REP.MC",
        "TEF.MC", "GRF.MC", "CLNX.MC", "LOG.MC", "SAB.MC",
        "MAP.MC", "ANA.MC", "ENG.MC", "RED.MC", "COL.MC",
        "MEL.MC", "ACX.MC", "VIS.MC", "SCYR.MC", "FDR.MC",
        "NTGY.MC", "MRL.MC", "UNI.MC", "CIE.MC", "PHM.MC",
        "ROVI.MC", "GEST.MC", "IDR.MC", "EBRO.MC", "ENC.MC",
    ],
}


def rank_companies(
    provider=None,
    years: int = 5,
    limit: int = 25,
) -> dict[str, list[tuple[str, float]]]:
    """Ordena las candidatas por rentabilidad total histórica."""

    if years < 1 or limit < 1:
        raise ValueError("years y limit deben ser positivos.")

    provider = provider or YahooFinanceProvider()

    end_date = date.today()
    start_date = end_date - timedelta(days=365 * years)
    end_exclusive = end_date + timedelta(days=1)

    start = start_date.isoformat()
    end = end_exclusive.isoformat()

    rankings = {}

    for category, tickers in COMPANY_UNIVERSE.items():
        frames = []

        # Se usan lotes para reducir problemas con descargas grandes.
        for offset in range(0, len(tickers), 10):
            batch = tickers[offset:offset + 10]

            try:
                data = provider.download_prices(batch, start, end)
                if not data.empty:
                    frames.append(data)
            except Exception:
                # Recuperación individual si falla el lote.
                for ticker in batch:
                    try:
                        data = provider.download_prices(
                            [ticker], start, end
                        )
                        if not data.empty:
                            frames.append(data)
                    except Exception:
                        continue

        if not frames:
            rankings[category] = []
            continue

        historical = pd.concat(frames, ignore_index=True)
        results = []

        for ticker, group in historical.groupby("ticker"):
            group = group.sort_values("date").copy()

            price_column = "adj_close"
            if (
                price_column not in group.columns
                or group[price_column].notna().sum() < 2
            ):
                price_column = "close"

            prices = pd.to_numeric(
                group[price_column], errors="coerce"
            ).dropna()

            if len(prices) < 2:
                continue

            valid_dates = pd.to_datetime(
                group.loc[prices.index, "date"]
            )

            # Exigir aproximadamente cinco años de historial.
            if (
                valid_dates.iloc[0].date() > start_date + timedelta(days=90)
                or valid_dates.iloc[-1].date() < end_date - timedelta(days=10)
            ):
                continue

            first_price = float(prices.iloc[0])
            last_price = float(prices.iloc[-1])

            if first_price <= 0 or last_price <= 0:
                continue

            performance = last_price / first_price - 1
            results.append((ticker, performance))

        rankings[category] = sorted(
            results,
            key=lambda item: item[1],
            reverse=True,
        )[:limit]

    return rankings


def generate_proposals(
    rankings: dict[str, list[tuple[str, float]]],
    rng=None,
) -> dict[str, list[str]]:
    """Genera propuestas A-E de cinco activos y Z diversificada."""

    rng = rng or random

    proposals = {}

    for category in CATEGORIES:
        available = rankings.get(category, [])
        tickers = [item[0] for item in available]

        if len(tickers) < 5:
            raise ValueError(
                f"La categoría {CATEGORIES[category]} solo tiene "
                f"{len(tickers)} compañías válidas; se necesitan al menos 5."
            )

        proposals[category] = rng.sample(tickers, 5)

    # Una compañía aleatoria de cada categoría.
    proposals["Z"] = [
        rng.choice([item[0] for item in rankings[category]])
        for category in CATEGORIES
    ]

    return proposals
