import pytest

from core import modelo, solo


@pytest.fixture(autouse=True)
def _memorias_limpas():
    # memórias de processo do motor: cada teste começa sem resultados de outro (que pode ter trocado o balanço ou a rede)
    modelo._memo_perdas.clear()
    solo._falhas.clear()
    yield
