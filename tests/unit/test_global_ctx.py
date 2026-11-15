from pathlib import Path

from core import global_ctx

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "faostat.csv"


def test_retorno_faostat():
    assert global_ctx.linhas_pais("BR", FIXTURE) == {
        "Milho": {"produtividade_t_ha": 6.0, "preco_usd_t": 180.0},
        "Sorgo": {"produtividade_t_ha": 4.0, "preco_usd_t": 150.0},
    }
    assert global_ctx.linhas_pais("KE", FIXTURE) == {}


def test_linhas_pais_sem_arquivo(tmp_path):
    assert global_ctx.linhas_pais("BR", tmp_path / "ausente.csv") == {}
