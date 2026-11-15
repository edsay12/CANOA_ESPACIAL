"""Fotos da fazenda, descrição visual e situação hídrica."""

import base64
import sqlite3
from datetime import UTC, timedelta
from pathlib import Path

import openai

from bot_logica.conversa import dividir
from bot_logica.idioma import t
from core.erros import ErroFonteDados

PASTA_FOTOS = Path(__file__).resolve().parent.parent / "data" / "fotos"


def maior_foto(variantes):
    """Seleciona a variante de maior resolução, independentemente da ordem."""
    return max(variantes, key=lambda foto: foto.width * foto.height)


class VisaoGroq:
    """Adaptador para o modelo de visão compatível com Chat Completions."""

    def __init__(self, cliente, modelo):
        self.cliente = cliente.with_options(
            base_url="https://api.groq.com/openai/v1", max_retries=0
        )
        self.modelo = modelo

    def __call__(self, conteudo, idioma):
        imagem = base64.b64encode(conteudo).decode("ascii")
        instrucao = (
            f"Responda no idioma {idioma}. Descreva apenas o que é visível: cultura, cor das folhas, "
            "murcha e solo exposto. Não faça diagnóstico nem atribua causas."
        )
        resposta = self.cliente.chat.completions.create(
            model=self.modelo,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instrucao},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{imagem}"},
                        },
                    ],
                }
            ],
            timeout=30,
        )
        texto = resposta.choices[0].message.content
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError("Descrição de imagem vazia")
        return texto.strip()


def _resposta(texto, lang):
    partes = dividir(texto)
    aviso = t("confirme_campo", lang)
    if partes and len(partes[-1]) + 2 + len(aviso) <= 4096:
        partes[-1] += f"\n\n{aviso}"
    else:
        partes.append(aviso)
    return partes


class Fotos:
    def __init__(self, db, descrever, alertas, pasta_fotos=PASTA_FOTOS):
        self.db = db
        self.descrever = descrever
        self.alertas = alertas
        self.pasta_fotos = Path(pasta_fotos)

    def tratar_foto(self, chat_id, conteudo, legenda, lang, agora):
        fazenda = self.db.fazenda_por_chat(chat_id)
        if fazenda is None:
            return _resposta(t("pedir_localizacao", lang), lang)
        instante = (
            agora.replace(tzinfo=UTC) if agora.tzinfo is None else agora.astimezone(UTC)
        )
        arquivo = None
        try:
            self.pasta_fotos.mkdir(parents=True, exist_ok=True)
            while True:
                caminho = (
                    self.pasta_fotos
                    / f"{fazenda['id']}_{instante:%Y%m%d_%H%M%S_%f}.jpg"
                )
                try:
                    destino = caminho.open("xb")
                    arquivo = caminho
                    break
                except FileExistsError:
                    instante += timedelta(microseconds=1)
            with destino:
                destino.write(conteudo)
            descricao = self.descrever(conteudo, lang)
            if not isinstance(descricao, str) or not descricao.strip():
                raise ValueError("Descrição de imagem vazia")
            self.db.salvar_observacao(
                fazenda["id"], legenda or "", str(arquivo), descricao
            )
        except (
            OSError,
            sqlite3.Error,
            openai.APIError,
            RuntimeError,
            ValueError,
            IndexError,
        ):
            if arquivo is not None:
                arquivo.unlink(missing_ok=True)
            return _resposta(t("foto_falhou", lang), lang)

        partes = [descricao]
        for inscricao in self.db.listar_alertas():
            vinculo = inscricao.get("fazenda_id")
            legado_mesma_area = (
                vinculo is None
                and str(inscricao.get("chat_id")) == str(chat_id)
                and inscricao.get("lat") == fazenda["lat"]
                and inscricao.get("lon") == fazenda["lon"]
            )
            if vinculo != fazenda["id"] and not legado_mesma_area:
                continue
            try:
                situacao = self.alertas.situacao(
                    fazenda["lat"],
                    fazenda["lon"],
                    inscricao["cultura"],
                    inscricao["data_plantio"],
                    agora,
                )
                partes.append(
                    t(
                        "foto_situacao",
                        lang,
                        cultura=inscricao["cultura"],
                        ks=situacao["ks"],
                    )
                )
            except (ErroFonteDados, ValueError):
                partes.append(
                    t("foto_situacao_indisponivel", lang, cultura=inscricao["cultura"])
                )
        return _resposta("\n\n".join(partes), lang)
