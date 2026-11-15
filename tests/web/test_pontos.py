"""Testes unitarios de web/pontos.py (T2: C3, C37)."""

from __future__ import annotations

from web.pontos import DEMO, normalizar


def test_clique_arredonda_2_casas() -> None:
    """C3 (SITE-03): Arredonda latitude e longitude para 2 casas decimais."""
    assert normalizar(-17.8049, -50.9183) == (-17.8, -50.92)


def test_longitude_normalizada() -> None:
    """C37 (SITE-37): Normaliza longitude fora de [-180, 180] antes de arredondar."""
    assert normalizar(10, 190) == (10.0, -170.0)
    assert normalizar(-5.123, -190.004) == (-5.12, 170.0)


def test_pontos_demo_quatro_regioes() -> None:
    """Confere os 4 botoes de exemplo e suas coordenadas."""
    assert list(DEMO.keys()) == [
        "Rio Verde (BR)",
        "Nakuru (KE)",
        "Ludhiana (IN)",
        "Ames (US)",
    ]
    assert DEMO["Rio Verde (BR)"] == (-17.80, -50.92)
    assert DEMO["Nakuru (KE)"] == (-0.30, 36.07)
    assert DEMO["Ludhiana (IN)"] == (30.90, 75.85)
    assert DEMO["Ames (US)"] == (42.03, -93.62)
