from web.mapa import clicar, marcador


def test_clique_normaliza_longitude_e_arredonda():
    assert clicar({"last_clicked": {"lat": -17.806, "lng": 309.084}}) == (-17.81, -50.92)
    assert clicar({"last_clicked": None}) is None


def test_mapa_so_tem_o_marcador_selecionado():
    assert not marcador(None).get_bounds()[0][0]
    atual = marcador((-17.8, -50.92))
    substituto = marcador((42.03, -93.62))
    assert atual.get_bounds() == [[-17.8, -50.92], [-17.8, -50.92]]
    assert substituto.get_bounds() == [[42.03, -93.62], [42.03, -93.62]]


def test_mapa_real_com_busca_que_seleciona_o_ponto():
    from web.mapa import mapa_mundi

    html = mapa_mundi("en").get_root().render()
    assert "tile.openstreetmap.org" in html
    assert "Search a city or place" in html
    assert 'mapa.fire("click", {latlng: e.geocode.center})' in html
