"""Camada de servico da interface com reuso de resultados na sessao."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from core import clima as _clima
from core import contexto as _contexto
from core import db as _db
from core import modelo as _modelo


def _motor_padrao() -> Any:
    """Agrupa as 4 chamadas publicas do motor."""
    return SimpleNamespace(
        contexto=getattr(_contexto, "contexto", None),
        clima_mudou=getattr(_clima, "clima_mudou", None),
        ranking_safra=getattr(_modelo, "ranking_safra", None),
        planos_rotacao=getattr(_modelo, "planos_rotacao", None),
    )


def _chave_pesos(
    prioridades: dict[str, float] | None,
) -> tuple[tuple[str, float], ...] | None:
    if prioridades is None:
        return None
    return tuple(sorted((str(k), float(v)) for k, v in prioridades.items()))


def db_disponivel(db: Any = _db) -> bool:
    """Retorna True se o modulo db expuser criar_fazenda e listar_observacoes."""
    if db is None:
        return False
    return callable(getattr(db, "criar_fazenda", None)) and callable(
        getattr(db, "listar_observacoes", None)
    )


class Servico:
    """Encapsula chamadas ao motor e ao banco com cache em memoria na sessao."""

    def __init__(
        self,
        motor: Any = None,
        db: Any = _db,
        memoria: dict[tuple[Any, ...], Any] | None = None,
        fazendas: dict[tuple[float, float], int] | None = None,
    ) -> None:
        self.motor = motor if motor is not None else _motor_padrao()
        self.db = db
        self.memoria: dict[tuple[Any, ...], Any] = (
            memoria if memoria is not None else {}
        )
        self.fazendas: dict[tuple[float, float], int] = (
            fazendas if fazendas is not None else {}
        )

    def contexto(self, lat: float, lon: float) -> dict[str, Any]:
        chave = ("contexto", round(float(lat), 2), round(float(lon), 2))
        if chave not in self.memoria:
            self.memoria[chave] = self.motor.contexto(lat, lon)
        return self.memoria[chave]

    def clima(
        self, lat: float, lon: float, idioma: str = "pt"
    ) -> dict[str, Any]:
        chave = ("clima", round(float(lat), 2), round(float(lon), 2), idioma)
        if chave not in self.memoria:
            self.memoria[chave] = self.motor.clima_mudou(
                lat, lon, idioma=idioma
            )
        return self.memoria[chave]

    def ranking(
        self,
        lat: float,
        lon: float,
        data_semeadura: str,
        prioridades: dict[str, float] | None = None,
        idioma: str = "pt",
    ) -> dict[str, Any]:
        chave = (
            "ranking",
            round(float(lat), 2),
            round(float(lon), 2),
            data_semeadura,
            _chave_pesos(prioridades),
            idioma,
        )
        if chave not in self.memoria:
            self.memoria[chave] = self.motor.ranking_safra(
                lat,
                lon,
                data_semeadura=data_semeadura,
                prioridades=prioridades,
                idioma=idioma,
            )
        return self.memoria[chave]

    def planos(
        self,
        lat: float,
        lon: float,
        historico: list[str],
        prioridades: dict[str, float] | None = None,
        idioma: str = "pt",
    ) -> dict[str, Any]:
        chave = (
            "planos",
            round(float(lat), 2),
            round(float(lon), 2),
            tuple(historico),
            _chave_pesos(prioridades),
            idioma,
        )
        if chave not in self.memoria:
            self.memoria[chave] = self.motor.planos_rotacao(
                lat,
                lon,
                historico=historico,
                prioridades=prioridades,
                idioma=idioma,
            )
        return self.memoria[chave]

    def db_disponivel(self) -> bool:
        return db_disponivel(self.db)

    def fazenda(
        self, lat: float, lon: float, pais: str | None = None
    ) -> int | None:
        if not self.db_disponivel():
            return None
        ponto = (round(float(lat), 2), round(float(lon), 2))
        if ponto in self.fazendas:
            return self.fazendas[ponto]
        chave_mem = ("fazenda_id", ponto[0], ponto[1])
        if chave_mem in self.memoria:
            self.fazendas[ponto] = int(self.memoria[chave_mem])
            return self.fazendas[ponto]
        if pais is None:
            ctx = self.contexto(lat, lon)
            pais = str(ctx.get("pais", "BR"))
        novo_id = int(self.db.criar_fazenda(ponto[0], ponto[1], pais))
        self.fazendas[ponto] = novo_id
        self.memoria[chave_mem] = novo_id
        return novo_id

    def observacoes(self) -> list[dict[str, Any]]:
        if not self.db_disponivel():
            return []
        return list(self.db.listar_observacoes())