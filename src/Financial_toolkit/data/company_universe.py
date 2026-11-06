"""Universo estático de compañías para MIAX 15."""

from __future__ import annotations

import random


CATEGORIES = {
    "A": "Tecnología",
    "B": "Inteligencia artificial (IA)",
    "C": "Energía",
    "D": "Automotrices",
    "E": "Compañías españolas",
}


COMPANY_UNIVERSE = {
    "A": [
        "AAPL", "MSFT", "NVDA", "AVGO", "ORCL",
        "AMD", "QCOM", "TXN", "AMAT", "LRCX",
        "KLAC", "MU", "ADI", "INTU", "NOW",
        "CRM", "ADBE", "PANW", "CRWD", "ANET",
        "PLTR", "IBM", "CSCO", "ACN", "SHOP",
    ],
    "B": [
        "NVDA", "AMD", "AVGO", "MSFT", "GOOGL",
        "META", "AMZN", "ORCL", "PLTR", "TSM",
        "ASML", "ARM", "MU", "MRVL", "ANET",
        "SNPS", "CDNS", "IBM", "NOW", "CRM",
        "ADBE", "SMCI", "DELL", "QCOM", "INTC",
    ],
    "C": [
        "XOM", "CVX", "COP", "EOG", "OXY",
        "SLB", "BKR", "HAL", "FANG", "DVN",
        "APA", "EPD", "ET", "WMB", "KMI",
        "LNG", "EQT", "CTRA", "NEE", "CEG",
        "VST", "FSLR", "ENPH", "CNQ", "SHEL",
    ],
    "D": [
        "TSLA", "TM", "HMC", "F", "GM",
        "STLA", "RACE", "MBG.DE", "BMW.DE", "VOW3.DE",
        "7201.T", "7267.T", "7203.T", "7269.T", "7270.T",
        "005380.KS", "000270.KS", "1211.HK", "LI", "NIO",
        "XPEV", "RIVN", "LCID", "MBLY", "APTV",
    ],
    "E": [
        "IBE.MC", "ITX.MC", "SAN.MC", "BBVA.MC", "CABK.MC",
        "FER.MC", "ACS.MC", "AENA.MC", "ELE.MC", "REP.MC",
        "TEF.MC", "GRF.MC", "CLNX.MC", "LOG.MC", "SAB.MC",
        "MAP.MC", "ANA.MC", "ENG.MC", "RED.MC", "COL.MC",
        "MEL.MC", "ACX.MC", "VIS.MC", "SCYR.MC", "NTGY.MC",
    ],
}


def generate_proposals(
    universe: dict[str, list[str]] | None = None,
    rng=None,
) -> dict[str, list[str]]:
    """Genera cinco propuestas sectoriales y una cartera diversificada."""

    universe = COMPANY_UNIVERSE if universe is None else universe
    rng = random if rng is None else rng

    proposals = {}

    for category in CATEGORIES:
        available = universe.get(category, [])

        if len(available) < 5:
            raise ValueError(
                f"La categoría {CATEGORIES[category]} solo tiene "
                f"{len(available)} compañías; se necesitan al menos 5."
            )

        proposals[category] = rng.sample(available, 5)

    diversified = []
    for category in CATEGORIES:
        available = [
            ticker
            for ticker in universe[category]
            if ticker not in diversified
        ]

        if not available:
            raise ValueError(
                "No hay suficientes compañías distintas para "
                "generar la propuesta diversificada."
            )

        diversified.append(rng.choice(available))

    proposals["Z"] = diversified

    return proposals
