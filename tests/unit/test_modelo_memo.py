from core import culturas, modelo, power


def test_memoria_das_perdas_nao_mistura_series_nem_vaza_mutacao():
    serie = power.serie(-17.80, -50.92)  # cache versionado do ponto da demo
    milho = culturas.carregar()["Milho"]
    modelo._memo_perdas.clear()
    primeira = modelo._perdas(serie, milho, 100, -17.80, 2, 15)
    primeira[1995] = -1  # mexer no resultado não pode alterar a memória
    assert modelo._perdas(serie, milho, 100, -17.80, 2, 15)[1995] != -1
    seca = serie.assign(chuva=0.0)
    assert modelo._perdas(seca, milho, 100, -17.80, 2, 15) != modelo._perdas(serie, milho, 100, -17.80, 2, 15)
    assert len(modelo._memo_perdas) == 2
