from pathlib import Path

from core.adaptadores import brasil

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "brasil_municipal.csv"


def test_sem_arquivo_devolve_none(tmp_path):
    assert brasil.dados(-17.8, -50.92, tmp_path / "brasil_municipal.csv") is None


def test_com_arquivo_municipio_mais_proximo():
    d = brasil.dados(-17.6, -50.7, FIXTURE)
    assert d["municipio"] == "Rio Verde"
    assert d["culturas"] == ["Milho", "Sorgo"]
    assert d["produtividade"] == {"Milho": 6.5, "Sorgo": 4.2}
    assert d["preco"] == {"Milho": 900.0, "Sorgo": 750.0}
    assert brasil.dados(-23.0, -51.0, FIXTURE)["culturas"] == ["Soja"]
