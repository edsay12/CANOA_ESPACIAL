"""Série diária recente do NASA POWER com cache por dia e janela."""

from datetime import date, timedelta

from core import cache, power, validacao


def serie(lat, lon, dias=45, hoje=None):
    """Busca os últimos dias até hoje, inclusive, sem preencher dados ausentes."""
    validacao.ponto(lat, lon)
    if isinstance(dias, bool) or not isinstance(dias, int) or dias <= 0:
        raise ValueError("dias deve ser um inteiro positivo")
    hoje = hoje or date.today()
    inicio = hoje - timedelta(days=dias - 1)
    base = cache.caminho("recente", lat, lon)
    sufixo = "" if dias == 45 else f"_{dias}d"
    caminho = base.with_name(f"{base.stem}_{hoje:%Y%m%d}{sufixo}.json")
    dados = cache.ler(caminho)
    if dados is None:
        dados = power._baixar(
            lat, lon, inicio.strftime("%Y%m%d"), hoje.strftime("%Y%m%d")
        )
        cache.gravar(caminho, dados)
    return power._converter(dados)
