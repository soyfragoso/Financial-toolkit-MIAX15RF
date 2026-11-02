
import pytest

from Financial_toolkit.data.providers import DataProvider


def test_data_provider_is_abstract():
    """
    Comprueba que DataProvider no puede instanciarse
    directamente.
    """

    with pytest.raises(TypeError):
        DataProvider()


def test_data_provider_requires_download_prices():
    """
    Comprueba que una clase hija debe implementar
    download_prices().
    """

    class IncompleteProvider(DataProvider):
        pass

    with pytest.raises(TypeError):
        IncompleteProvider()


def test_data_provider_accepts_implemented_method():
    """
    Comprueba que una clase hija que implementa
    download_prices() sí puede instanciarse.
    """

    class MockProvider(DataProvider):

        def download_prices(self, tickers, start, end):
            return None

    provider = MockProvider()

    assert isinstance(provider, DataProvider)
    assert callable(provider.download_prices)

