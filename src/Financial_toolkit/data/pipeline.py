import pandas as pd

from Financial_toolkit.data.downloader import DataDownloader
from Financial_toolkit.data.preprocessing import DataPreprocessor
from Financial_toolkit.data.providers import DataProvider


class DataPipeline:
    """
    Coordina la descarga y el preprocesamiento de datos financieros.
    """

    def __init__(self, provider: DataProvider):
        self.downloader = DataDownloader(provider)
        self.preprocessor = DataPreprocessor()

    def run(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """
        Descarga y preprocesa datos para uno o varios activos.
        """

        raw_data = self.downloader.download(
            tickers=tickers,
            start=start,
            end=end,
        )

        return self.preprocessor.preprocess(raw_data)
