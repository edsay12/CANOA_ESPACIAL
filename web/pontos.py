"""Pontos de demonstracao e normalizacao de coordenadas para o site."""

from __future__ import annotations

DEMO: dict[str, tuple[float, float]] = {
    "Rio Verde (BR)": (-17.80, -50.92),
    "Nakuru (KE)": (-0.30, 36.07),
    "Ludhiana (IN)": (30.90, 75.85),
    "Ames (US)": (42.03, -93.62),
}


def normalizar(lat: float, lon: float) -> tuple[float, float]:
    """Traz longitude para [-180, 180] e arredonda lat/lon para 2 casas."""
    lon_norm = ((float(lon) + 180.0) % 360.0) - 180.0
    if lon_norm == -180.0 and lon > 0:
        lon_norm = 180.0
    return (round(float(lat), 2), round(lon_norm, 2))
