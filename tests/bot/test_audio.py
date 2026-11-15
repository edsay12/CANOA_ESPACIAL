from types import SimpleNamespace

import httpx
import openai

from bot_logica.audio import Audio, TranscritorGroq
from bot_logica.idioma import t
from bot_logica.limite import Limite


def test_transcreve_e_processa():
    chamadas = []

    class Conversa:
        def __init__(self):
            self.limite = Limite(maximo=1, relogio=lambda: 100)

        def texto(self, chat_id, texto, lang):
            assert self.limite.permitir(chat_id)
            chamadas.append((chat_id, texto, lang))
            return ["Resposta da conversa"]

    transcricoes = []
    audio = Audio(
        Conversa(),
        lambda conteudo: transcricoes.append(conteudo) or "  qual plantio?  ",
    )
    assert audio.tratar_voz(123, b"ogg", "es") == ["Resposta da conversa"]
    assert transcricoes == [b"ogg"]
    assert chamadas == [(123, "qual plantio?", "es")]

    class Cliente:
        def __init__(self):
            self.audio = SimpleNamespace(transcriptions=self)
            self.opcoes = None
            self.chamada = None

        def with_options(self, **kw):
            self.opcoes = kw
            return self

        def create(self, **kw):
            self.chamada = kw
            return SimpleNamespace(text="Transcrição")

    cliente = Cliente()
    transcritor = TranscritorGroq(cliente, "modelo-voz")
    assert transcritor(b"bytes", nome_arquivo="voz.oga") == "Transcrição"
    assert cliente.opcoes == {
        "base_url": "https://api.groq.com/openai/v1",
        "max_retries": 0,
    }
    assert cliente.chamada["file"] == ("voz.ogg", b"bytes", "audio/ogg")
    assert cliente.chamada["model"] == "modelo-voz" and cliente.chamada["timeout"] == 30
    assert (
        cliente.chamada["response_format"] == "json"
        and "language" not in cliente.chamada
    )
    transcritor(b"mp3", nome_arquivo="arquivo.mp3")
    assert cliente.chamada["file"] == ("arquivo.mp3", b"mp3", "audio/mpeg")
    audio_com_mp3 = Audio(Conversa(), transcritor)
    assert audio_com_mp3.tratar_voz(124, b"mp3", "pt", nome_arquivo="arquivo.mp3") == [
        "Resposta da conversa"
    ]
    assert cliente.chamada["file"] == ("arquivo.mp3", b"mp3", "audio/mpeg")
    assert chamadas[-1] == (124, "Transcrição", "pt")


def test_falha_transcricao():
    conversas = []
    conversa = SimpleNamespace(texto=lambda *args: conversas.append(args))
    request = httpx.Request(
        "POST", "https://api.groq.com/openai/v1/audio/transcriptions"
    )
    erros = [
        openai.APIConnectionError(request=request),
        openai.APITimeoutError(request=request),
        RuntimeError("segredo"),
    ]
    for lang in ("pt", "en", "es"):
        for erro in erros:

            def falhar(conteudo, falha=erro):
                raise falha

            assert Audio(conversa, falhar).tratar_voz(1, b"ogg", lang) == [
                t("audio_falhou", lang)
            ]
        for vazio in ("", "   ", None):
            assert Audio(
                conversa, lambda conteudo, resultado=vazio: resultado
            ).tratar_voz(1, b"ogg", lang) == [t("audio_falhou", lang)]
    audio = Audio(
        conversa,
        lambda conteudo: (_ for _ in ()).throw(AssertionError("não transcrever")),
    )
    assert audio.tratar_voz(1, b"", "pt") == [t("audio_falhou", "pt")]
    assert conversas == []


def test_erro_da_conversa_nao_e_mascarado():
    import pytest

    def falhar(*args):
        raise RuntimeError("erro interno da conversa")

    audio = Audio(SimpleNamespace(texto=falhar), lambda conteudo: "pergunta")
    with pytest.raises(RuntimeError, match="erro interno da conversa"):
        audio.tratar_voz(1, b"ogg", "pt")
