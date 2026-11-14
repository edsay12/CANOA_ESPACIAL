import pytest

from core import validacao


def test_ponto_fora_do_intervalo():
    for lat, lon in [(90.01, 0), (-90.01, 0), (0, 180.01), (0, -180.01)]:
        with pytest.raises(ValueError):
            validacao.ponto(lat, lon)
    for lat, lon in [(90, 180), (-90, -180), (-17.8, -50.92)]:
        assert validacao.ponto(lat, lon) is None


def test_data_mmdd_invalida():
    assert validacao.data_mmdd("03-15") == (3, 15)
    assert validacao.data_mmdd("12-31") == (12, 31)
    for s in ["13-01", "00-10", "02-30", "04-31", "3-15", "03/15", "2024-03-15", "", None, "ab-cd"]:
        with pytest.raises(ValueError):
            validacao.data_mmdd(s)


def test_pesos_invalidos():
    with pytest.raises(ValueError):
        validacao.pesos({"retorno": -0.1, "seguranca": 0.6, "solo": 0.5})
    with pytest.raises(ValueError):
        validacao.pesos({"retorno": 0, "seguranca": 0, "solo": 0})


def test_pesos_reescalados():
    p = validacao.pesos({"retorno": 2, "seguranca": 1, "solo": 1})
    assert p == pytest.approx({"retorno": 0.5, "seguranca": 0.25, "solo": 0.25})
    assert sum(p.values()) == pytest.approx(1)
    assert validacao.pesos(None) == pytest.approx({"retorno": 0.4, "seguranca": 0.4, "solo": 0.2})
