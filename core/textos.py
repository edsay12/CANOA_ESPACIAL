"""Frases do motor em pt, en e es; outro idioma usa en."""

TEXTOS = {
    "pt": {
        "resumo_clima": "{variavel} passou de {antes} em 1995–2009 para {depois} em 2010–2025.",
        "var_chuva": "A chuva da estação",
        "var_chuva_anual": "A chuva anual",
        "var_inicio": "O início da estação",
        "var_fim": "O fim da estação",
        "var_veranicos": "O número de veranicos",
        "var_calor": "O número de dias com 35 °C ou mais",
        "explicacao_safra": "faltou água em {depois} de {n_depois} anos desde 2010; antes eram {antes} de {n_antes}",
        "explicacao_plano": "{risco:+d} pontos de risco e {retorno:+.0f} {moeda}/ano de retorno frente ao plano atual",
        "explicacao_plano_sem_retorno": "{risco:+d} pontos de risco frente ao plano atual",
        "explicacao_plano_sem_atual": "{risco_abs}% de risco de quebra; o plano atual não tem parâmetros para comparar",
    },
    "en": {
        "resumo_clima": "{variavel} went from {antes} in 1995–2009 to {depois} in 2010–2025.",
        "var_chuva": "Season rainfall",
        "var_chuva_anual": "Annual rainfall",
        "var_inicio": "Season start",
        "var_fim": "Season end",
        "var_veranicos": "The number of dry spells",
        "var_calor": "The number of days at 35 °C or more",
        "explicacao_safra": "water fell short in {depois} of {n_depois} years since 2010; before it was {antes} of {n_antes}",
        "explicacao_plano": "{risco:+d} risk points and {retorno:+.0f} {moeda}/year of return versus the current plan",
        "explicacao_plano_sem_retorno": "{risco:+d} risk points versus the current plan",
        "explicacao_plano_sem_atual": "{risco_abs}% failure risk; the current plan has no parameters to compare",
    },
    "es": {
        "resumo_clima": "{variavel} pasó de {antes} en 1995–2009 a {depois} en 2010–2025.",
        "var_chuva": "La lluvia de la temporada",
        "var_chuva_anual": "La lluvia anual",
        "var_inicio": "El inicio de la temporada",
        "var_fim": "El fin de la temporada",
        "var_veranicos": "El número de veranillos",
        "var_calor": "El número de días con 35 °C o más",
        "explicacao_safra": "faltó agua en {depois} de {n_depois} años desde 2010; antes eran {antes} de {n_antes}",
        "explicacao_plano": "{risco:+d} puntos de riesgo y {retorno:+.0f} {moeda}/año de retorno frente al plan actual",
        "explicacao_plano_sem_retorno": "{risco:+d} puntos de riesgo frente al plan actual",
        "explicacao_plano_sem_atual": "{risco_abs}% de riesgo de pérdida; el plan actual no tiene parámetros para comparar",
    },
}


def t(chave, idioma, **valores):
    return TEXTOS.get(idioma, TEXTOS["en"])[chave].format(**valores)
