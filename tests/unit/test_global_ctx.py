from pathlib import Path

import pytest

from core import global_ctx

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "faostat.csv"


def test_retorno_faostat():
    assert global_ctx.linhas_pais("BR", FIXTURE) == {
        "Milho": {"produtividade_t_ha": 6.0, "preco_usd_t": 180.0},
        "Sorgo": {"produtividade_t_ha": 4.0, "preco_usd_t": 150.0},
    }
    valor, moeda = global_ctx.retorno("BR", "Milho", 0.25, FIXTURE)
    assert valor == pytest.approx(6.0 * 0.75 * 180)
    assert moeda == "USD"
    assert global_ctx.retorno("US", "Milho", 0, FIXTURE) == (pytest.approx(2200.0), "USD")


def test_sem_linha_retorno_none(tmp_path):
    assert global_ctx.retorno("BR", "Soja", 0.1, FIXTURE) == (None, None)
    assert global_ctx.retorno("KE", "Milho", 0.1, FIXTURE) == (None, None)
    assert global_ctx.linhas_pais("KE", FIXTURE) == {}
    assert global_ctx.retorno("BR", "Milho", 0.1, tmp_path / "ausente.csv") == (None, None)
