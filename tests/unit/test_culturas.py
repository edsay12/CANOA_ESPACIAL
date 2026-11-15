from pathlib import Path

from core import culturas

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "culturas.csv"


def test_carrega_csv_real_com_20_culturas():
    c = culturas.carregar()
    assert len(c) == 20
    assert {"Soja", "Milho"} <= set(c)
    assert c["Milho"]["kc_mid"] == 1.2
    assert c["Milho"]["dias_ini"] == 20
    assert c["Soja"]["dias_ini"] is None  # célula vazia vira None


def test_carrega_csv_de_fixture():
    c = culturas.carregar(FIXTURE)
    assert set(c) == {"Teste", "Incompleta"}
    t = c["Teste"]
    assert (t["dias_ini"], t["dias_des"], t["dias_mid"], t["dias_fim"]) == (20, 30, 40, 20)
    assert (t["kc_ini"], t["ky"], t["t_min_c"], t["t_max_c"]) == (0.3, 1.25, 10, None)
    assert culturas.completa(t)


def test_completa_falso_sem_campo_do_modelo():
    base = culturas.carregar(FIXTURE)["Teste"]
    assert not culturas.completa(culturas.carregar(FIXTURE)["Incompleta"])
    for campo in culturas.CAMPOS_MODELO:
        assert not culturas.completa({**base, campo: None}), campo
        sem = {k: v for k, v in base.items() if k != campo}
        assert not culturas.completa(sem), campo
