"""Regras de conversa compartilhadas pelos handlers do Telegram."""

from datetime import UTC, datetime

from bot_logica.idioma import t
from bot_logica.llm import LLMIndisponivel
from core import culturas
from core.erros import ErroFonteDados, ErroPontoInvalido


def dividir(texto, tamanho=4096):
    """Divide texto sem perdas em partes de até tamanho caracteres."""
    if tamanho <= 0:
        raise ValueError("tamanho deve ser positivo")
    return [
        texto[inicio : inicio + tamanho] for inicio in range(0, len(texto), tamanho)
    ]


def _hoje():
    return datetime.now(UTC).date()


class Conversa:
    def __init__(self, db, motor, assistente, limite, alertas, hoje=_hoje):
        self.db, self.motor, self.assistente = db, motor, assistente
        self.limite, self.alertas, self.hoje = limite, alertas, hoje

    def _permitir(self, chat_id, lang):
        return None if self.limite.permitir(chat_id) else [t("limite", lang)]

    def start(self, chat_id, args, lang):
        if bloqueio := self._permitir(chat_id, lang):
            return bloqueio
        if not args:
            return [t("boas_vindas", lang)]
        try:
            identificador = int(args[0])
            if not 0 < identificador <= 2**63 - 1:
                raise ValueError("id inválido")
            fazenda = self.db.fazenda(identificador)
        except (ValueError, TypeError):
            fazenda = None
        if fazenda is None:
            return [t("fazenda_nao_encontrada", lang)]
        self.db.vincular_chat(identificador, chat_id)
        try:
            clima = self.motor.clima_mudou(fazenda["lat"], fazenda["lon"], idioma=lang)
            return dividir(clima["resumo"])
        except (ErroFonteDados, ErroPontoInvalido, ValueError):
            return [t("motor_indisponivel", lang)]

    def localizacao(self, chat_id, lat, lon, lang):
        if bloqueio := self._permitir(chat_id, lang):
            return bloqueio
        try:
            contexto = self.motor.contexto(lat, lon)
            pais = contexto["pais"]["iso2"]
            if pais is None:
                raise ErroPontoInvalido("fora de terra")
        except ErroPontoInvalido:
            return [t("ponto_invalido", lang)]
        except (ErroFonteDados, ValueError):
            return [t("motor_indisponivel", lang)]
        try:
            clima = self.motor.clima_mudou(lat, lon, idioma=lang)
            ranking = self.motor.ranking_safra(
                lat, lon, data_semeadura=self.hoje().strftime("%m-%d"), idioma=lang
            )
            item = ranking["itens"][0] if ranking["itens"] else None
        except ErroPontoInvalido:
            return [t("ponto_invalido", lang)]
        except (ErroFonteDados, ValueError):
            clima = item = None
        fazenda = self.db.fazenda_por_chat(chat_id)
        if fazenda:
            self.db.atualizar_local(fazenda["id"], lat, lon, pais)
        else:
            self.db.criar_fazenda(lat, lon, pais, chat_id)
        if clima is None or item is None:
            return [t("motor_indisponivel", lang)]
        resposta = f"{clima['resumo']}\n{t('melhor_cultura', lang, cultura=item['cultura'], risco=item['risco_pct'])}"
        if item.get("preliminar"):
            resposta += f"\n{t('aviso_preliminar', lang)}"
        return dividir(f"{resposta}\n{t('dados_fonte', lang)}")

    def texto(self, chat_id, texto, lang, limite_verificado=False):
        if not limite_verificado and (bloqueio := self._permitir(chat_id, lang)):
            return bloqueio
        fazenda = self.db.fazenda_por_chat(chat_id)
        if fazenda is None:
            return [t("pedir_localizacao", lang)]
        if self.assistente is None:
            return [t("llm_indisponivel", lang)]
        try:
            return dividir(self.assistente.responder(chat_id, texto, fazenda, lang))
        except LLMIndisponivel:
            return [t("llm_indisponivel", lang)]

    def alerta(self, chat_id, args, lang):
        if bloqueio := self._permitir(chat_id, lang):
            return bloqueio
        fazenda = self.db.fazenda_por_chat(chat_id)
        if fazenda is None:
            return [t("pedir_localizacao", lang)]
        catalogo = {
            nome: cultura
            for nome, cultura in culturas.carregar().items()
            if culturas.completa(cultura)
        }
        formato = t("alerta_formato", lang, culturas=", ".join(catalogo))
        if len(args) < 2:
            return dividir(formato)
        nome = " ".join(args[:-1]).strip().casefold()
        cultura = next((chave for chave in catalogo if chave.casefold() == nome), None)
        try:
            texto_data = args[-1]
            data = datetime.strptime(texto_data, "%d/%m/%Y").date()
            if data.strftime("%d/%m/%Y") != texto_data:
                raise ValueError("data inválida")
        except (ValueError, TypeError):
            return dividir(formato)
        if cultura is None:
            return dividir(formato)
        self.db.inscrever_alerta(fazenda["id"], cultura, data.isoformat(), idioma=lang)
        return [t("alerta_ok", lang, cultura=cultura, data=texto_data)]

    def testar_alerta(self, chat_id, lang):
        if bloqueio := self._permitir(chat_id, lang):
            return bloqueio
        if self.db.fazenda_por_chat(chat_id) is None:
            return [t("pedir_localizacao", lang)]
        resultados = self.alertas.verificar(
            self.db, self.hoje(), forcar=True, chat_id=chat_id
        )
        if not resultados:
            return [t("sem_alertas", lang)]
        return [
            parte
            for item in resultados
            for parte in dividir(t(item["mensagem_chave"], lang, **item["valores"]))
        ]
