"""Textos fixos da interface do site em pt, en e es; idioma desconhecido usa pt."""

IDIOMAS = {
    "Português": "pt",
    "English": "en",
    "Español": "es",
}

TEXTOS = {
    "pt": {
        "idioma": "Idioma",
        "abertura": "Clique no mapa ou escolha um exemplo",
        "carregando": "Calculando com 30 anos de dados da NASA…",
        "selo_municipal": "Dados municipais",
        "selo_pais": "Dados do país",
        "selo_clima": "Estimado pelo clima",
        "erro_ponto": "Esse ponto fica fora de terra firme. Escolha outro lugar.",
        "erro_fonte": "Os dados da NASA estão indisponíveis agora. Tente de novo em alguns minutos.",
        "aba_clima": "Seu clima mudou",
        "aba_plantar": "O que plantar",
        "aba_planos": "Planos de rotação",
        "ind_chuva": "Chuva da estação (mm)",
        "ind_chuva_anual": "Chuva anual (mm)",
        "ind_inicio": "Início das chuvas",
        "ind_fim": "Fim das chuvas",
        "ind_veranicos": "Veranicos por estação",
        "ind_calor": "Dias ≥ 35 °C",
        "nota_anual": "Sem estação chuvosa definida: comparando o ano inteiro",
        "anos_sem_estacao": "Anos sem estação chuvosa detectada: {n}",
        "data_semeadura": "Data de semeadura",
        "prio_retorno": "Retorno",
        "prio_seguranca": "Segurança contra seca",
        "prio_solo": "Saúde do solo",
        "risco_quebra": "Risco de quebra: {n}%",
        "retorno_com_moeda": "Retorno: {valor} {moeda}",
        "retorno_sem_dado": "Retorno: sem dado",
        "culturas_ignoradas": "Culturas sem dados suficientes",
        "prioridades_vazias": "Escolha pelo menos uma prioridade",
        "ranking_vazio": "Nenhuma cultura com dados suficientes para este lugar",
        "safra_1": "Safra 1",
        "safra_2": "Safra 2",
        "safra_3": "Safra 3",
        "historico_incompleto": "Informe o que você plantou nas últimas 3 safras",
        "plano_atual": "Seu plano atual",
        "por_que_confiar": "Por que confiar",
        "limites": (
            "Limites do modelo: usa dados regionais (~50 km); "
            "não diagnostica pragas ou doenças; "
            "a janela de plantio é estimada pelo clima; "
            "não considera irrigação."
        ),
        "atualizar_fotos": "Atualizar fotos",
        "alertas_telegram": "Receber alertas no Telegram",
    },
    "en": {
        "idioma": "Language",
        "abertura": "Click on the map or choose an example",
        "carregando": "Calculating with 30 years of NASA data…",
        "selo_municipal": "Municipal data",
        "selo_pais": "Country data",
        "selo_clima": "Estimated by climate",
        "erro_ponto": "This point is off land. Choose another place.",
        "erro_fonte": "NASA data is unavailable right now. Try again in a few minutes.",
        "aba_clima": "Your climate changed",
        "aba_plantar": "What to plant",
        "aba_planos": "Rotation plans",
        "ind_chuva": "Season rainfall (mm)",
        "ind_chuva_anual": "Annual rainfall (mm)",
        "ind_inicio": "Rainy season start",
        "ind_fim": "Rainy season end",
        "ind_veranicos": "Dry spells per season",
        "ind_calor": "Days ≥ 35 °C",
        "nota_anual": "No defined rainy season: comparing the whole year",
        "anos_sem_estacao": "Years without detected rainy season: {n}",
        "data_semeadura": "Sowing date",
        "prio_retorno": "Return",
        "prio_seguranca": "Drought safety",
        "prio_solo": "Soil health",
        "risco_quebra": "Crop failure risk: {n}%",
        "retorno_com_moeda": "Return: {valor} {moeda}",
        "retorno_sem_dado": "Return: no data",
        "culturas_ignoradas": "Crops without enough data",
        "prioridades_vazias": "Choose at least one priority",
        "ranking_vazio": "No crop with enough data for this place",
        "safra_1": "Season 1",
        "safra_2": "Season 2",
        "safra_3": "Season 3",
        "historico_incompleto": "Enter what you planted in the last 3 seasons",
        "plano_atual": "Your current plan",
        "por_que_confiar": "Why trust this",
        "limites": (
            "Model limits: uses regional data (~50 km); "
            "does not diagnose pests or diseases; "
            "planting window is estimated by climate; "
            "does not consider irrigation."
        ),
        "atualizar_fotos": "Refresh photos",
        "alertas_telegram": "Receive alerts on Telegram",
    },
    "es": {
        "idioma": "Idioma",
        "abertura": "Haz clic en el mapa o elige un ejemplo",
        "carregando": "Calculando con 30 años de datos de la NASA…",
        "selo_municipal": "Datos municipales",
        "selo_pais": "Datos del país",
        "selo_clima": "Estimado por el clima",
        "erro_ponto": "Este punto está fuera de tierra firme. Elige otro lugar.",
        "erro_fonte": "Los datos de la NASA no están disponibles ahora. Inténtalo de nuevo en unos minutos.",
        "aba_clima": "Tu clima cambió",
        "aba_plantar": "Qué plantar",
        "aba_planos": "Planes de rotación",
        "ind_chuva": "Lluvia de la temporada (mm)",
        "ind_chuva_anual": "Lluvia anual (mm)",
        "ind_inicio": "Inicio de las lluvias",
        "ind_fim": "Fin de las lluvias",
        "ind_veranicos": "Veranillos por temporada",
        "ind_calor": "Días ≥ 35 °C",
        "nota_anual": "Sin estación lluviosa definida: comparando todo el año",
        "anos_sem_estacao": "Años sin estación lluviosa detectada: {n}",
        "data_semeadura": "Fecha de siembra",
        "prio_retorno": "Retorno",
        "prio_seguranca": "Seguridad contra sequía",
        "prio_solo": "Salud del suelo",
        "risco_quebra": "Riesgo de pérdida: {n}%",
        "retorno_com_moeda": "Retorno: {valor} {moeda}",
        "retorno_sem_dado": "Retorno: sin datos",
        "culturas_ignoradas": "Cultivos sin datos suficientes",
        "prioridades_vazias": "Elige al menos una prioridad",
        "ranking_vazio": "Ningún cultivo con datos suficientes para este lugar",
        "safra_1": "Cosecha 1",
        "safra_2": "Cosecha 2",
        "safra_3": "Cosecha 3",
        "historico_incompleto": "Informa lo que plantaste en las últimas 3 cosechas",
        "plano_atual": "Tu plan actual",
        "por_que_confiar": "Por qué confiar",
        "limites": (
            "Límites del modelo: usa datos regionales (~50 km); "
            "no diagnostica plagas ni enfermedades; "
            "la ventana de siembra es estimada por el clima; "
            "no considera riego."
        ),
        "atualizar_fotos": "Actualizar fotos",
        "alertas_telegram": "Recibir alertas en Telegram",
    },
}


def t(chave: str, idioma: str = "pt", **valores) -> str:
    """Retorna o texto traduzido para a chave e idioma informados (padrão: pt)."""
    tabela = TEXTOS.get(idioma, TEXTOS["pt"])
    texto = tabela[chave]
    return texto.format(**valores) if valores else texto
