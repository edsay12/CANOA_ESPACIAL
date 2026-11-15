"""Idioma do usuário do Telegram e textos fixos do bot em pt/en/es (BOT-22).

Contrato: idioma(language_code) -> "pt"|"en"|"es" · t(chave, idioma, **valores) -> str
Os textos em pt são os da spec; o tom final é da Cecilia (só este arquivo muda).
"""

TEXTOS = {
    "pt": {
        "boas_vindas": (
            "Olá! Eu sou o assistente da Canoa Espacial. Uso 30 anos de dados da NASA para mostrar como o clima "
            "da sua região mudou e o que plantar. Mande sua localização (📎 → Localização) para começar. "
            "Fotos e localização ficam guardadas até o fim do evento."
        ),
        "pedir_localizacao": "Mande sua localização (📎 → Localização) para eu conhecer sua fazenda.",
        "fazenda_nao_encontrada": "Não encontrei essa fazenda. Mande sua localização.",
        "ponto_invalido": "Esse ponto fica fora de terra firme. Mande outra localização.",
        "dados_fonte": "Dados: NASA POWER",
        "limite": "Você atingiu o limite de 20 mensagens por hora. Tente de novo mais tarde.",
        "llm_indisponivel": "O assistente está indisponível agora. Tente de novo em alguns minutos.",
        "confirme_campo": "Confirme no campo: pode ser falta d'água, praga, doença ou compactação.",
        "audio_falhou": "Não consegui entender o áudio. Pode escrever ou mandar de novo?",
        "alerta_formato": "Culturas conhecidas: {culturas}. Use o formato: /alerta Milho 15/02/2026",
        "alerta_ok": "Pronto! Vou avisar se faltar água para {cultura} semeada em {data}.",
        "alerta_falta_agua": (
            "⚠️ Falta d'água chegando para {cultura}: o solo está secando e a floração começa em {dias} dias. "
            "Os dados da NASA chegam com alguns dias de atraso."
        ),
        "aviso_preliminar": "parâmetros genéricos da FAO, não calibrados para a região",
    },
    "en": {
        "boas_vindas": (
            "Hi! I am the Canoa Espacial assistant. I use 30 years of NASA data to show how your area's climate "
            "changed and what to plant. Send your location (📎 → Location) to start. "
            "Photos and location are kept until the end of the event."
        ),
        "pedir_localizacao": "Send your location (📎 → Location) so I can find your farm.",
        "fazenda_nao_encontrada": "I could not find that farm. Send your location.",
        "ponto_invalido": "That point is not on land. Send another location.",
        "dados_fonte": "Data: NASA POWER",
        "limite": "You reached the limit of 20 messages per hour. Try again later.",
        "llm_indisponivel": "The assistant is unavailable right now. Try again in a few minutes.",
        "confirme_campo": "Check in the field: it may be lack of water, pests, disease or compaction.",
        "audio_falhou": "I could not understand the audio. Can you type it or send it again?",
        "alerta_formato": "Known crops: {culturas}. Use the format: /alerta Milho 15/02/2026",
        "alerta_ok": "Done! I will warn you if {cultura} sown on {data} runs short of water.",
        "alerta_falta_agua": (
            "⚠️ Water shortage ahead for {cultura}: the soil is drying and flowering starts in {dias} days. "
            "NASA data arrive a few days late."
        ),
        "aviso_preliminar": "generic FAO parameters, not calibrated for the region",
    },
    "es": {
        "boas_vindas": (
            "¡Hola! Soy el asistente de Canoa Espacial. Uso 30 años de datos de la NASA para mostrar cómo cambió "
            "el clima de tu región y qué sembrar. Envía tu ubicación (📎 → Ubicación) para empezar. "
            "Las fotos y la ubicación se guardan hasta el fin del evento."
        ),
        "pedir_localizacao": "Envía tu ubicación (📎 → Ubicación) para conocer tu finca.",
        "fazenda_nao_encontrada": "No encontré esa finca. Envía tu ubicación.",
        "ponto_invalido": "Ese punto no está en tierra firme. Envía otra ubicación.",
        "dados_fonte": "Datos: NASA POWER",
        "limite": "Alcanzaste el límite de 20 mensajes por hora. Inténtalo más tarde.",
        "llm_indisponivel": "El asistente no está disponible ahora. Inténtalo en unos minutos.",
        "confirme_campo": "Confírmalo en el campo: puede ser falta de agua, plaga, enfermedad o compactación.",
        "audio_falhou": "No entendí el audio. ¿Puedes escribirlo o enviarlo de nuevo?",
        "alerta_formato": "Cultivos conocidos: {culturas}. Usa el formato: /alerta Milho 15/02/2026",
        "alerta_ok": "¡Listo! Te avisaré si falta agua para {cultura} sembrado el {data}.",
        "alerta_falta_agua": (
            "⚠️ Se acerca falta de agua para {cultura}: el suelo se está secando y la floración empieza en {dias} días. "
            "Los datos de la NASA llegan con unos días de retraso."
        ),
        "aviso_preliminar": "parámetros genéricos de la FAO, no calibrados para la región",
    },
}


def idioma(language_code):
    """pt*/en*/es* do Telegram (ex.: "pt-BR", "es-419") viram pt/en/es; qualquer outro, ou None, vira en."""
    base = (language_code or "").lower()[:2]
    return base if base in ("pt", "es") else "en"


def t(chave, idioma, **valores):
    return TEXTOS.get(idioma, TEXTOS["en"])[chave].format(**valores)
