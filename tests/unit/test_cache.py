import json

import pytest

from core import cache


def test_caminho_usa_prefixo_e_duas_casas(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "PASTA", tmp_path)
    assert cache.caminho("power", -17.8, -50.923) == tmp_path / "power_-17.80_-50.92.json"


def test_ler_devolve_none_para_json_invalido_ou_ausente(tmp_path):
    ruim = tmp_path / "x.json"
    ruim.write_text("{nao e json", encoding="utf-8")
    assert cache.ler(ruim) is None
    assert cache.ler(tmp_path / "ausente.json") is None


def test_gravacao_atomica(tmp_path, monkeypatch):
    destino = tmp_path / "power_1.00_2.00.json"
    cache.gravar(destino, {"v": 1})
    assert cache.ler(destino) == {"v": 1}

    def dump_que_falha(dados, f):
        f.write('{"v": 2, "parcial')
        raise OSError("disco cheio")

    monkeypatch.setattr(json, "dump", dump_que_falha)
    with pytest.raises(OSError):
        cache.gravar(destino, {"v": 2})
    assert cache.ler(destino) == {"v": 1}
    assert [p.name for p in tmp_path.iterdir()] == [destino.name]

    novo = tmp_path / "novo.json"
    with pytest.raises(OSError):
        cache.gravar(novo, {"v": 3})
    assert not novo.exists()
