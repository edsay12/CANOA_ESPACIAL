from types import SimpleNamespace

import httpx
import openai
import pytest

from bot_logica.idioma import t
from bot_logica.llm import Assistente, LLMIndisponivel, prompt_sistema


class ClienteFalso:
    def __init__(self):
        self.responses = self
        self.chamadas = []
        self.opcoes = []
        self.resultado = "resposta final"
        self.status = None
        self.erro = None

    def with_options(self, **opcoes):
        self.opcoes.append(opcoes)
        return self

    def create(self, **kwargs):
        self.chamadas.append(kwargs)
        if self.erro:
            raise self.erro
        return SimpleNamespace(output_text=self.resultado, status=self.status)


FAZENDA = {"id": 42, "lat": -12.5, "lon": -45.75}


def _assistente(cliente):
    return Assistente(cliente, "modelo-chat", "https://mcp.example/mcp", "segredo")


def test_pergunta_usa_responses_com_remote_mcp():
    cliente = ClienteFalso()
    assistente = _assistente(cliente)
    resposta = assistente.responder(111, "O que plantar?", FAZENDA, "pt")
    assert resposta == "resposta final"
    assert cliente.opcoes == [
        {"base_url": "https://api.groq.com/openai/v1", "max_retries": 0}
    ]
    chamada = cliente.chamadas[0]
    assert chamada["model"] == "modelo-chat"
    assert chamada["timeout"] == 30
    assert chamada["input"] == [{"role": "user", "content": "O que plantar?"}]
    ferramenta = chamada["tools"][0]
    assert len(chamada["tools"]) == 1
    assert ferramenta["type"] == "mcp"
    assert ferramenta["server_url"] == "https://mcp.example/mcp"
    assert ferramenta["server_label"]
    assert ferramenta["headers"] == {"Authorization": "Bearer segredo"}
    assert ferramenta["require_approval"] == "never"
    assert ferramenta["server_description"]
    assert "store" not in chamada and "previous_response_id" not in chamada


def test_prompt_sistema_regras():
    prompt = prompt_sistema(FAZENDA, "es")
    assert "id=42" in prompt
    assert "latitude=-12.5" in prompt
    assert "longitude=-45.75" in prompt
    assert "Responda no idioma es" in prompt
    assert "Todo número deve vir de uma ferramenta; nunca invente valores" in prompt
    assert "Encerre a resposta citando as fontes dos dados" in prompt
    cliente = ClienteFalso()
    _assistente(cliente).responder(111, "Pergunta", FAZENDA, "es")
    assert cliente.chamadas[0]["instructions"] == prompt


def test_memoria_ultimas_6():
    cliente = ClienteFalso()
    assistente = _assistente(cliente)
    for numero in range(4):
        cliente.resultado = f"resposta {numero}"
        assert (
            assistente.responder(111, f"pergunta {numero}", FAZENDA, "pt")
            == f"resposta {numero}"
        )
    cliente.resultado = "resposta de outro chat"
    assistente.responder(222, "outro chat", FAZENDA, "en")
    assert cliente.chamadas[-1]["input"] == [{"role": "user", "content": "outro chat"}]
    assistente.responder(111, "pergunta atual", FAZENDA, "pt")
    assert cliente.chamadas[-1]["input"] == [
        {"role": "user", "content": "pergunta 1"},
        {"role": "assistant", "content": "resposta 1"},
        {"role": "user", "content": "pergunta 2"},
        {"role": "assistant", "content": "resposta 2"},
        {"role": "user", "content": "pergunta 3"},
        {"role": "assistant", "content": "resposta 3"},
        {"role": "user", "content": "pergunta atual"},
    ]


def test_falha_groq_mensagem_erro():
    cliente = ClienteFalso()
    assistente = _assistente(cliente)
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/responses")
    response = httpx.Response(429, request=request)
    erros = [
        openai.APIConnectionError(request=request),
        openai.APITimeoutError(request=request),
        openai.RateLimitError("segredo", response=response, body=None),
    ]
    for idioma, erro in zip(("pt", "en", "es"), erros, strict=True):
        cliente.erro = erro
        with pytest.raises(LLMIndisponivel) as captura:
            assistente.responder(1, "pergunta falha", FAZENDA, idioma)
        assert str(captura.value) == t("llm_indisponivel", idioma)
        assert "segredo" not in str(captura.value)
        assert captura.value.__suppress_context__
    cliente.erro = None
    cliente.resultado = "texto parcial"
    for status in ("failed", "incomplete"):
        cliente.status = status
        with pytest.raises(LLMIndisponivel) as captura:
            assistente.responder(1, "pergunta parcial", FAZENDA, "pt")
        assert str(captura.value) == t("llm_indisponivel", "pt")
    cliente.status = "completed"
    cliente.resultado = "   "
    with pytest.raises(LLMIndisponivel):
        assistente.responder(1, "pergunta vazia", FAZENDA, "pt")
    cliente.resultado = "ok"
    assistente.responder(1, "nova pergunta", FAZENDA, "pt")
    assert cliente.chamadas[-1]["input"] == [
        {"role": "user", "content": "nova pergunta"}
    ]
