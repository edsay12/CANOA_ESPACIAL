"""Transcrição de voz e encaminhamento à conversa."""

from pathlib import Path

import openai

from bot_logica.idioma import t


class TranscritorGroq:
    """Adapta áudio em memória para o endpoint de transcrição da Groq."""

    def __init__(self, cliente, modelo="whisper-large-v3-turbo"):
        self.cliente = cliente.with_options(
            base_url="https://api.groq.com/openai/v1", max_retries=0
        )
        self.modelo = modelo

    def __call__(self, conteudo, nome_arquivo="voz.ogg"):
        sufixo = Path(nome_arquivo).suffix.lower()
        tipos = {
            ".oga": (".ogg", "audio/ogg"),
            ".ogg": (".ogg", "audio/ogg"),
            ".mp3": (".mp3", "audio/mpeg"),
            ".wav": (".wav", "audio/wav"),
            ".m4a": (".m4a", "audio/mp4"),
            ".flac": (".flac", "audio/flac"),
            ".webm": (".webm", "audio/webm"),
            ".mp4": (".mp4", "audio/mp4"),
        }
        if sufixo not in tipos:
            raise ValueError("Formato de áudio não suportado")
        extensao, tipo = tipos[sufixo]
        nome = f"{Path(nome_arquivo).stem}{extensao}"
        resposta = self.cliente.audio.transcriptions.create(
            model=self.modelo,
            file=(nome, conteudo, tipo),
            response_format="json",
            timeout=30,
        )
        return resposta.text


class Audio:
    def __init__(self, conversa, transcrever):
        self.conversa = conversa
        self.transcrever = transcrever

    def tratar_voz(self, chat_id, conteudo, lang, nome_arquivo=None):
        return self.processar_voz(chat_id, conteudo, lang, nome_arquivo)[1]

    def processar_voz(
        self, chat_id, conteudo, lang, nome_arquivo=None, limite_verificado=False
    ):
        """Retorna transcrição e resposta sem executar o fluxo duas vezes."""
        if not conteudo:
            return None, [t("audio_falhou", lang)]
        try:
            texto = (
                self.transcrever(conteudo)
                if nome_arquivo is None
                else self.transcrever(conteudo, nome_arquivo=nome_arquivo)
            )
            if not isinstance(texto, str) or not texto.strip():
                raise ValueError("Transcrição vazia")
        except (openai.APIError, TimeoutError, OSError, RuntimeError, ValueError):
            return None, [t("audio_falhou", lang)]
        texto = texto.strip()
        if limite_verificado:
            return texto, self.conversa.texto(
                chat_id, texto, lang, limite_verificado=True
            )
        return texto, self.conversa.texto(chat_id, texto, lang)
