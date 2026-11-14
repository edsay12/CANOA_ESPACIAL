"""Exceções do domínio do motor."""


class ErroFonteDados(Exception):
    """Fonte externa (NASA POWER, SoilGrids) indisponível e sem cache."""


class ErroPontoInvalido(Exception):
    """Ponto onde o motor não calcula, por exemplo fora de terra."""
