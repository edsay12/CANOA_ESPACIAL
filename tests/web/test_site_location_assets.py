from pathlib import Path
from xml.etree import ElementTree

ATIVOS = Path(__file__).resolve().parents[2] / "assets" / "site-location"


def test_svg_da_tela_preservam_dimensoes_do_figma():
    icones = ("arrow", "chevron", "example-pin", "globe", "hand", "location-pin", "logo")
    dimensoes = dict.fromkeys(icones, ("24", "24"))
    dimensoes.update({"world-desktop": ("1258", "629"), "world-mobile": ("322", "161")})

    for nome, tamanho in dimensoes.items():
        raiz = ElementTree.parse(ATIVOS / f"{nome}.svg").getroot()
        assert raiz.tag == "{http://www.w3.org/2000/svg}svg"
        assert (raiz.get("width"), raiz.get("height")) == tamanho
        assert list(raiz)
