from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pandas as pd
import pytest

from bot_logica.idioma import t
from core import alertas, balanco, culturas, recente, solo
from core.erros import ErroFonteDados


def _serie(inicio, fim):
    datas = pd.date_range(inicio, fim)
    return pd.DataFrame({"data": datas, "chuva": 0.0, "tmax": 30.0, "tmin": 20.0})


def test_balanco_desde_plantio(monkeypatch):
    hoje = date(2026, 11, 15)
    plantio = hoje - timedelta(days=60)
    recebidas = []
    dados = _serie(plantio - timedelta(days=3), hoje)
    dados.loc[dados.index[-2:], ["tmax", "tmin"]] = float("nan")

    def serie(lat, lon, dias, hoje):
        assert dias >= 61
        assert hoje == date(2026, 11, 15)
        return dados

    def calcular(janela, cultura, cad_mm, lat):
        recebidas.append(janela.copy())
        assert cad_mm == 100 and lat == -12
        return {"ks": 0.3}

    monkeypatch.setattr(recente, "serie", serie)
    monkeypatch.setattr(solo, "agua_disponivel", lambda lat, lon: {"cad_mm": 100})
    monkeypatch.setattr(balanco, "balanco_parcial", calcular, raising=False)
    resultado = alertas.situacao(-12, -45, "Soja", plantio.isoformat(), hoje)
    assert resultado["ks"] == 0.3
    assert recebidas[0]["data"].iloc[0] == pd.Timestamp(plantio)
    assert recebidas[0]["data"].iloc[-1] == pd.Timestamp(hoje - timedelta(days=2))
    dados = dados.iloc[5:]
    with pytest.raises(ValueError):
        alertas.situacao(-12, -45, "Soja", plantio.isoformat(), hoje)
    assert len(recebidas) == 1


def test_envia_quando_ks_baixo_perto_do_florescimento(monkeypatch):
    hoje = date(2026, 11, 15)
    cultura = culturas.carregar()["Soja"]
    meio = int(cultura["dias_ini"]) + int(cultura["dias_des"])
    monkeypatch.setattr(
        recente,
        "serie",
        lambda lat, lon, dias, hoje: _serie(hoje - timedelta(days=dias - 1), hoje),
    )
    monkeypatch.setattr(solo, "agua_disponivel", lambda lat, lon: {"cad_mm": 100})
    ks = [0.69]
    monkeypatch.setattr(
        balanco, "balanco_parcial", lambda *args: {"ks": ks[0]}, raising=False
    )

    def situacao(dias):
        return alertas.situacao(
            1, 2, "Soja", (hoje - timedelta(days=meio - dias)).isoformat(), hoje
        )

    assert situacao(15)["alerta"] and situacao(0)["alerta"]
    assert not situacao(16)["alerta"] and not situacao(-1)["alerta"]
    ks[0] = 0.7
    assert not situacao(10)["alerta"]
    ks[0] = 0.69
    item = {
        "id": 4,
        "fazenda_id": 8,
        "chat_id": "123",
        "lat": 1,
        "lon": 2,
        "cultura": "Soja",
        "data_plantio": (hoje - timedelta(days=meio - 10)).isoformat(),
        "ativo": 1,
        "ultimo_envio": None,
    }
    banco = SimpleNamespace(listar_alertas=lambda ativos: [item])
    resultado = alertas.verificar(banco, hoje)
    assert resultado == [
        {
            "chat_id": "123",
            "alerta_id": 4,
            "mensagem_chave": "alerta_falta_agua",
            "valores": {"cultura": "Soja", "ks": 0.69, "dias": 10},
        }
    ]
    assert "atraso" in t(
        resultado[0]["mensagem_chave"], "pt", **resultado[0]["valores"]
    )


def test_nao_repete_em_7_dias(monkeypatch):
    agora = datetime(2026, 11, 15, 10, tzinfo=UTC)

    def item(id_, fazenda, chat, ativo, envio=None, lat=1):
        return {
            "id": id_,
            "fazenda_id": fazenda,
            "chat_id": chat,
            "lat": lat,
            "lon": 2,
            "cultura": "Soja",
            "data_plantio": "2026-10-01",
            "ativo": ativo,
            "ultimo_envio": envio,
        }

    itens = [
        item(1, 10, "1", 1),
        item(2, 10, "1", 0, (agora - timedelta(days=6)).isoformat()),
        item(3, 20, "2", 1),
        item(4, 20, "2", 1),
        item(5, 30, None, 1),
        item(6, None, "3", 1, lat=3),
        item(7, None, "3", 1, lat=4),
    ]
    banco = SimpleNamespace(listar_alertas=lambda ativos: itens)
    monkeypatch.setattr(
        alertas,
        "situacao",
        lambda *args: {"ks": 0.4, "dias_ate_meio": 5, "alerta": True},
    )
    resultado = alertas.verificar(banco, agora)
    assert [a["alerta_id"] for a in resultado] == [3, 6, 7]
    assert [
        a["alerta_id"] for a in alertas.verificar(banco, agora, forcar=True, chat_id=1)
    ] == [1]
    assert [
        a["alerta_id"] for a in alertas.verificar(banco, agora, forcar=True, chat_id=2)
    ] == [3, 4]
    itens[1]["ultimo_envio"] = (agora - timedelta(days=7)).isoformat()
    assert [a["alerta_id"] for a in alertas.verificar(banco, agora)] == [1, 3, 6, 7]
    itens[1]["ultimo_envio"] = (
        agora - timedelta(days=7) + timedelta(seconds=1)
    ).isoformat()
    assert [a["alerta_id"] for a in alertas.verificar(banco, agora)] == [3, 6, 7]
    itens.append(item(8, None, "2", 0, (agora - timedelta(days=1)).isoformat()))
    assert [a["alerta_id"] for a in alertas.verificar(banco, agora)] == [6, 7]
    assert [
        a["alerta_id"] for a in alertas.verificar(banco, agora, forcar=True, chat_id=2)
    ] == [3, 4]


def test_falhas_isoladas_e_futuro(monkeypatch):
    hoje = date(2026, 11, 15)
    with pytest.raises(ValueError):
        alertas.situacao(1, 2, "Soja", "2026-11-16", hoje)
    itens = [
        {
            "id": i,
            "fazenda_id": i,
            "chat_id": str(i),
            "lat": i,
            "lon": 2,
            "cultura": "Soja",
            "data_plantio": "2026-10-01",
            "ativo": 1,
            "ultimo_envio": None,
        }
        for i in (1, 2)
    ]

    def situacao(lat, *args):
        if lat == 1:
            raise ErroFonteDados("offline")
        return {"ks": 0.2, "dias_ate_meio": 2, "alerta": True}

    monkeypatch.setattr(alertas, "situacao", situacao)
    assert [
        a["alerta_id"]
        for a in alertas.verificar(
            SimpleNamespace(listar_alertas=lambda ativos: itens), hoje
        )
    ] == [2]


def test_ks_real_usa_balanco_fao(monkeypatch):
    hoje = date(2026, 11, 15)
    cultura = dict(culturas.carregar()["Soja"], raiz_m=0.5, p_deplecao=0.4)
    monkeypatch.setattr(culturas, "carregar", lambda: {"Soja": cultura})
    monkeypatch.setattr(
        recente, "serie", lambda lat, lon, dias, hoje: _serie(hoje, hoje)
    )
    monkeypatch.setattr(solo, "agua_disponivel", lambda lat, lon: {"cad_mm": 100})
    resultado = alertas.situacao(-12, -45, "Soja", hoje.isoformat(), hoje)
    # TAW=50, Dr inicial=25 e RAW=20: Ks=(50-25)/(50-20).
    assert resultado["ks"] == pytest.approx(25 / 30)
    assert resultado["alerta"] is False
