"""Testes unitarios de web/servico.py (T3: C9, C36)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from web.servico import Servico, db_disponivel


class MotorFake:
    """Motor falso que conta quantas vezes cada funcao foi chamada."""

    def __init__(self) -> None:
        self.chamadas: dict[str, int] = {
            "contexto": 0,
            "clima": 0,
            "ranking": 0,
            "planos": 0,
        }

    def contexto(self, lat: float, lon: float) -> dict[str, Any]:
        self.chamadas["contexto"] += 1
        return {"pais": "BR", "nivel_dados": "municipal"}

    def clima_mudou(
        self, lat: float, lon: float, idioma: str = "pt"
    ) -> dict[str, Any]:
        self.chamadas["clima"] += 1
        return {"modo": "estacao", "idioma": idioma}

    def ranking_safra(
        self,
        lat: float,
        lon: float,
        data_semeadura: str,
        prioridades: dict[str, float] | None = None,
        idioma: str = "pt",
    ) -> dict[str, Any]:
        self.chamadas["ranking"] += 1
        return {"ranking": [], "data": data_semeadura}

    def planos_rotacao(
        self,
        lat: float,
        lon: float,
        historico: list[str],
        prioridades: dict[str, float] | None = None,
        idioma: str = "pt",
    ) -> dict[str, Any]:
        self.chamadas["planos"] += 1
        return {"planos": [], "historico": list(historico)}


class DbFake:
    """Banco falso para testar reuso de fazenda e listagem de observacoes."""

    def __init__(self) -> None:
        self.chamadas_criar = 0

    def criar_fazenda(self, lat: float, lon: float, pais: str) -> int:
        self.chamadas_criar += 1
        return 42

    def listar_observacoes(self) -> list[dict[str, Any]]:
        return [{"id": 1, "lat": -17.8, "lon": -50.92}]


def test_reusa_resultado_na_sessao() -> None:
    """C9 (SITE-09): Mesma chamada na sessao nao chama o motor de novo."""
    motor = MotorFake()
    memoria: dict[tuple[Any, ...], Any] = {}
    srv = Servico(motor=motor, memoria=memoria)

    pesos = {"retorno": 40, "seguranca": 40, "solo": 20}
    r1 = srv.ranking(-17.8, -50.92, "03-01", prioridades=pesos, idioma="pt")
    r2 = srv.ranking(-17.8, -50.92, "03-01", prioridades=pesos, idioma="pt")
    assert r1 == r2
    assert motor.chamadas["ranking"] == 1

    c1 = srv.clima(-17.8, -50.92, idioma="pt")
    c2 = srv.clima(-17.8, -50.92, idioma="pt")
    assert c1 == c2
    assert motor.chamadas["clima"] == 1

    p1 = srv.planos(
        -17.8, -50.92, ["soja", "milho", "sorgo"], prioridades=pesos
    )
    p2 = srv.planos(
        -17.8, -50.92, ["soja", "milho", "sorgo"], prioridades=pesos
    )
    assert p1 == p2
    assert motor.chamadas["planos"] == 1


def test_fazenda_reusada_na_sessao() -> None:
    """C36 (SITE-36): Chamar fazenda 2x no mesmo ponto cria apenas 1 registro."""
    motor = MotorFake()
    db = DbFake()
    srv = Servico(motor=motor, db=db)

    id1 = srv.fazenda(-17.8, -50.92, pais="BR")
    id2 = srv.fazenda(-17.8, -50.92, pais="BR")

    assert id1 == 42
    assert id2 == 42
    assert db.chamadas_criar == 1


def test_db_disponivel_quando_funcoes_existem() -> None:
    """SITE-35: Verifica deteccao de banco disponivel vs ausente."""
    assert db_disponivel(None) is False
    assert db_disponivel(SimpleNamespace()) is False
    assert db_disponivel(DbFake()) is True