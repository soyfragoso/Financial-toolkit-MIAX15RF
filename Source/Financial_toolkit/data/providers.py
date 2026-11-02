
from abc import ABC, abstractmethod
import pandas as pd


class DataProvider(ABC):
    """
    Clase abstracta que define la interfaz común
    para todos los proveedores de datos financieros.
    """

    @abstractmethod
    def download_prices(
        self,
        tickers: list[str],
        start: str,
        end: str
    ) -> pd.DataFrame:
        """
        Descarga precios históricos de uno o varios activos.

        Parameters
        ----------
        tickers : list[str]
            Lista de símbolos financieros.
        start : str
            Fecha inicial (YYYY-MM-DD).
        end : str
            Fecha final (YYYY-MM-DD).

        Returns
        -------
        pd.DataFrame
            DataFrame con los precios históricos.
        """
        pass

