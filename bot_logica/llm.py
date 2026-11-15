"""Assistente Groq por Responses API e ferramenta Remote MCP."""

from collections import defaultdict, deque

import openai

from bot_logica.idioma import t


class LLMIndisponivel(Exception):
    """A Groq não retornou uma resposta utilizável."""


def prompt_sistema(fazenda, idioma):
    return (
        "Você é o assistente agrícola da Canoa Espacial. "
        f"Fazenda: id={fazenda['id']}, latitude={fazenda['lat']}, longitude={fazenda['lon']}. "
        "Use esse id nas operações relativas à fazenda. "
        f"Responda no idioma {idioma}. "
        "Todo número deve vir de uma ferramenta; nunca invente valores. "
        "Encerre a resposta citando as fontes dos dados."
    )


class Memoria:
    """Últimas n mensagens concluídas para cada chat, em ordem cronológica."""

    def __init__(self, n=6):
        self._mensagens = defaultdict(lambda: deque(maxlen=n))

    def obter(self, chat_id):
        return list(self._mensagens[chat_id])

    def adicionar(self, chat_id, papel, conteudo):
        self._mensagens[chat_id].append({"role": papel, "content": conteudo})


class Assistente:
    def __init__(self, cliente, modelo, mcp_url, mcp_token):
        self.cliente = cliente.with_options(
            base_url="https://api.groq.com/openai/v1", max_retries=0
        )
        self.modelo = modelo
        self.mcp_url = mcp_url
        self.mcp_token = mcp_token
        self.memoria = Memoria(6)

    def responder(self, chat_id, pergunta, fazenda, idioma):
        mensagens = [
            *self.memoria.obter(chat_id),
            {"role": "user", "content": pergunta},
        ]
        try:
            resposta = self.cliente.responses.create(
                model=self.modelo,
                instructions=prompt_sistema(fazenda, idioma),
                input=mensagens,
                tools=[
                    {
                        "type": "mcp",
                        "server_label": "canoa_espacial",
                        "server_url": self.mcp_url,
                        "server_description": "Ferramentas agrícolas, climáticas e de registro de campo.",
                        "headers": {"Authorization": f"Bearer {self.mcp_token}"},
                        "require_approval": "never",
                    }
                ],
                timeout=30,
            )
        except (openai.APIError, TimeoutError):
            raise LLMIndisponivel(t("llm_indisponivel", idioma)) from None
        texto = resposta.output_text
        if (
            getattr(resposta, "status", None) not in (None, "completed")
            or not isinstance(texto, str)
            or not texto.strip()
        ):
            raise LLMIndisponivel(t("llm_indisponivel", idioma))
        self.memoria.adicionar(chat_id, "user", pergunta)
        self.memoria.adicionar(chat_id, "assistant", texto)
        return texto
