# Bot (Telegram + MCP + SQLite) Specification

**Approved**: 2026-11-14 - user: "aprovo"

## Problem Statement

O produtor no campo não usa site nem mapa, mas usa o celular. O bot do Telegram leva o motor até ele: manda a localização, pergunta no próprio idioma, envia fotos da lavoura e recebe alertas de falta d'água. A LLM só entende a pergunta e redige a resposta; os números vêm do motor pelas ferramentas do servidor MCP (AD-001, AD-002, AD-004). O banco SQLite liga o bot ao site.

## Goals

- [ ] "O que planto depois da soja?" em PT e "what should I plant after soybean?" em EN respondem com os mesmos números do site em < 15 s.
- [ ] Uma foto enviada no Telegram vira um pin no mapa do site.
- [ ] Nenhuma ferramenta do MCP responde sem o token.

## Out of Scope

| Feature | Reason |
| ------- | ------ |
| Cálculo agronômico | Motor (AD-004) |
| Respostas sem LLM quando a Groq falha | Usuário: "Só mensagem de erro" |
| Comando /apagar e expiração automática | Usuário: dados apagados manualmente ao fim do hackathon |
| Diagnóstico de praga/doença pela foto | AD-004 |
| Resposta em áudio (TTS) | Deferred Ideas |
| WhatsApp | Decisão anterior pelo Telegram (AD-001) |
| Várias fazendas por usuário | MVP: uma fazenda por chat |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Acesso | Público | user: "Qualquer um, 20 msgs/hora (Recommended)" | y |
| Limite | 20 mensagens por usuário por hora (janela móvel de 60 min) | mesma resposta | y |
| Retenção | Até o fim do hackathon; apagar `db.sqlite` e `data/fotos/` manualmente | user: "Até o fim do hackathon" | y |
| Falha da Groq | Só mensagem de erro | user: "Só mensagem de erro" | y |
| Segurança do MCP | `Authorization: Bearer <MCP_TOKEN>` | user: "Token secreto no cabeçalho (Recommended)" | y |
| Contagem do limite | Em memória do processo; reinício zera | Simples para 48h; sem tabela extra | n |
| Uma fazenda por chat | Nova localização atualiza a fazenda do chat | Produtor do MVP tem uma área | n |
| Aviso de privacidade | O /start diz que fotos e localização ficam guardadas até o fim do evento | Usuário enviará dados pessoais | n |
| Horário dos alertas | Uma vez por dia às 10:00 UTC | Um único job global | n |
| Intervalo entre alertas | No máximo 1 alerta por fazenda a cada 7 dias | Evita repetir o mesmo aviso | n |
| Clima recente | POWER diário dos últimos 45 dias, cache de 1 dia | A série do motor termina em 2025-12-31 | n |
| Memória da conversa | Últimas 6 mensagens por chat, em memória | Contexto curto para a LLM | n |
| Timeout da Groq | 30 s | Telegram precisa de resposta rápida | n |
| Modelos da Groq | Nomes vêm do `.env` (`GROQ_MODEL_CHAT`, `GROQ_MODEL_VISION`, `GROQ_MODEL_AUDIO`) | Nomes mudam; o time confirma antes | n |

**Open questions:** none - all resolved or logged above (required before the spec is confirmed).

---

## User Stories

### P1: Banco compartilhado ⭐ MVP

**User Story**: As a dev do site e do bot, I want one SQLite store for farms, observations and alert subscriptions so that what happens in the bot shows up on the site.

**Why P1**: Liga os dois sistemas (SITE-32..36) e guarda a fazenda de cada chat.

**Acceptance Criteria**:

1. WHEN `db.criar_fazenda(lat, lon, pais, chat_id=None)` is called THEN the system SHALL store the farm in `db.sqlite` and return its integer id.
2. WHEN `db.fazenda_por_chat(chat_id)` is called for a chat with a farm THEN the system SHALL return that farm's id, lat, lon and pais; for a chat without a farm it SHALL return None.
3. WHEN `db.vincular_chat(fazenda_id, chat_id)` is called THEN the system SHALL make that farm the chat's farm.
4. WHEN `db.salvar_observacao(fazenda_id, texto, foto_path, descricao_ia)` is called THEN the system SHALL store the observation with the current UTC timestamp and `listar_observacoes()` SHALL return it with the farm's lat and lon.
5. WHEN `db.inscrever_alerta(fazenda_id, cultura, data_plantio)` is called THEN the system SHALL store an active subscription and `listar_alertas()` SHALL return it.
6. The system SHALL create the database file and its tables on first use when they do not exist.
7. The system SHALL open a new connection per operation so that the site process and the bot process can use the file at the same time.
8. The system SHALL keep all user data only in `db.sqlite` and `data/fotos/`.

**Independent Test**: Criar fazenda → salvar observação → listar e encontrar com lat/lon, em dois processos.

---

### P1: Servidor MCP ⭐ MVP

**User Story**: As a LLM da Groq, I want the motor exposed as MCP tools so that I answer with real numbers instead of inventing them.

**Why P1**: Sem ferramentas a LLM não tem números (AD-004).

**Acceptance Criteria**:

1. The system SHALL expose over HTTP the tools `contexto`, `clima_mudou`, `ranking_safra`, `planos_rotacao`, `janela_plantio`, `info_cultura`, `registrar_observacao` and `inscrever_alerta`, each with a description in Portuguese and English.
2. WHEN a tool is called THEN the system SHALL return the motor's result for those arguments, including its `fontes` when the motor returns them.
3. IF a request lacks the header `Authorization: Bearer <MCP_TOKEN>` or carries a different token THEN the system SHALL reject it with HTTP 401 and run no tool.
4. IF the motor raises `ErroPontoInvalido`, `ErroFonteDados` or `ValueError` THEN the tool SHALL return an error result with the exception's message and no stack trace.
5. WHEN `info_cultura(nome)` is called with a crop from `culturas.csv` THEN the system SHALL return its papel, familia, fixa_n, climas, tolerancia_seca, efeito_solo and fonte.
6. IF `info_cultura(nome)` is called with an unknown crop THEN the system SHALL return an error result listing the known crop names.

**Independent Test**: Listar as 8 ferramentas com o token; chamar sem token e receber 401.

---

### P1: Conversa no Telegram ⭐ MVP

**User Story**: As a produtor, I want to send my location and ask questions in my language so that I get the recommendation without a website.

**Why P1**: É o canal do produtor no campo.

**Acceptance Criteria**:

1. WHEN a user sends `/start` THEN the bot SHALL reply with the welcome text, ask for the location and state that photos and location are kept until the end of the event.
2. WHEN a user sends `/start <id>` with an existing farm id THEN the bot SHALL link that farm to the chat and reply with that farm's "seu clima mudou" summary.
3. IF the id in `/start <id>` does not exist THEN the bot SHALL reply "Não encontrei essa fazenda. Mande sua localização." and link nothing.
4. WHEN a user sends a location THEN the bot SHALL create or update the chat's farm and reply with the motor's `clima_mudou` resumo and the top item of `ranking_safra` for today's date, followed by "Dados: NASA POWER".
5. WHEN a user sends a text question and the chat has a farm THEN the bot SHALL send it to the Groq Responses API with the Remote MCP tool pointing to `MCP_PUBLIC_URL` with the `MCP_TOKEN` header, and reply with the model's final text.
6. The bot SHALL send to the model a system prompt that contains the farm's lat, lon and id, the reply language, the rule "Todo número deve vir de uma ferramenta; nunca invente valores" and the instruction to end with the data sources.
7. IF a user sends a text question and the chat has no farm THEN the bot SHALL reply asking for the location and not call the model.
8. The bot SHALL reply in Portuguese, English or Spanish according to the Telegram `language_code` (pt*, en*, es*), and in English for any other code.
9. The bot SHALL send the model the last 6 messages of the chat as context.
10. IF a user has sent 20 messages in the last 60 minutes THEN the bot SHALL reply "Você atingiu o limite de 20 mensagens por hora. Tente de novo mais tarde." and not process the message.
11. IF the Groq call fails, times out after 30 s or returns a rate-limit error THEN the bot SHALL reply "O assistente está indisponível agora. Tente de novo em alguns minutos."
12. WHERE `USE_REMOTE_MCP=false` the bot SHALL call the Groq Chat Completions API with the same tools as function definitions, run the matching motor function locally for each tool call, and stop after 5 tool calls per message.

**Independent Test**: /start → localização → pergunta em PT e em EN com os mesmos números do site.

---

### P2: Fotos da lavoura

**User Story**: As a produtor, I want to send a photo of my field so that it is recorded and I get an honest hint of what may be happening.

**Why P2**: Liga campo e mapa (barreira 2), mas o MVP vive sem.

**Acceptance Criteria**:

1. WHEN a user with a farm sends a photo THEN the bot SHALL save the largest size under `data/fotos/<fazenda_id>_<timestamp>.jpg`.
2. WHEN a photo is saved THEN the bot SHALL send it to the Groq vision model with the instruction to describe the crop, leaf color, wilting and bare soil without giving a diagnosis.
3. WHEN the description arrives THEN the bot SHALL store the observation with the photo caption (or empty text) and the description.
4. WHERE the farm has an active alert subscription the bot SHALL add the current water status of that crop from the recent-climate check.
5. The bot SHALL end every photo reply with "Confirme no campo: pode ser falta d'água, praga, doença ou compactação."
6. IF a user without a farm sends a photo THEN the bot SHALL ask for the location and not save the photo.

---

### P2: Alertas de falta d'água

**User Story**: As a produtor, I want to be warned when my crop is running out of water before flowering so that I can act.

**Why P2**: Uso contínuo do bot; não é o núcleo do desafio.

**Acceptance Criteria**:

1. WHEN a user with a farm sends `/alerta <cultura> <DD/MM/AAAA>` THEN the bot SHALL subscribe the farm for that crop and sowing date and confirm.
2. IF the crop is unknown or the date is invalid THEN the bot SHALL reply with the known crops and the format "/alerta Milho 15/02/2026" and subscribe nothing.
3. The system SHALL run the alert check once a day at 10:00 UTC.
4. WHEN the check runs THEN the system SHALL compute, for each active subscription, the water balance from the sowing date to the latest NASA POWER day using the recent-climate series.
5. WHEN Ks < 0.7 and the crop's mid stage starts in 15 days or less THEN the system SHALL send the alert to the farm's chat, stating that NASA data have a delay of a few days.
6. IF the farm received an alert in the last 7 days THEN the system SHALL not send another.
7. WHEN `core.recente.serie(lat, lon, dias=45)` is called THEN the system SHALL return the last 45 days of POWER daily data with the same columns as `power.serie`, cached for 1 day.
8. WHEN a user sends `/testar_alerta` THEN the bot SHALL run the check for that chat's subscriptions immediately, ignoring the 7-day rule.

---

### P2: Áudio

**User Story**: As a produtor, I want to ask by voice so that I don't need to type.

**Why P2**: Acessibilidade (barreira 6).

**Acceptance Criteria**:

1. WHEN a user sends a voice message THEN the bot SHALL transcribe it with the Groq audio model and process the transcription as a text question.
2. IF the transcription fails or is empty THEN the bot SHALL reply "Não consegui entender o áudio. Pode escrever ou mandar de novo?"

---

## Edge Cases

- IF `MCP_TOKEN`, `GROQ_API_KEY` or `TELEGRAM_BOT_TOKEN` is missing at startup THEN the process SHALL exit with a message naming the missing variable.
- IF the motor raises `ErroPontoInvalido` for a sent location THEN the bot SHALL reply "Esse ponto fica fora de terra firme. Mande outra localização." and keep the previous farm.
- WHEN the model's reply exceeds 4096 characters THEN the bot SHALL split it into several Telegram messages.
- IF a motor result returned by a tool contains an item with `preliminar = true` THEN the tool result SHALL include `aviso` with "parâmetros genéricos da FAO, não calibrados para a região" in the user's language.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| -------------- | ----- | ----- | ------ |
| BOT-01 | P1: Banco — criar fazenda | Execute | Verified |
| BOT-02 | P1: Banco — fazenda por chat | Execute | Verified |
| BOT-03 | P1: Banco — vincular chat | Execute | Verified |
| BOT-04 | P1: Banco — observações | Execute | Verified |
| BOT-05 | P1: Banco — alertas | Execute | Verified |
| BOT-06 | P1: Banco — cria tabelas | Execute | Verified |
| BOT-07 | P1: Banco — conexão por operação | Execute | Verified |
| BOT-08 | P1: Banco — dados só em db e fotos | Execute | Verified |
| BOT-09 | P1: MCP — 8 ferramentas | Design | Pending |
| BOT-10 | P1: MCP — resultado do motor | Execute | Verified |
| BOT-11 | P1: MCP — token / 401 | Design | Pending |
| BOT-12 | P1: MCP — erros legíveis | Execute | Verified |
| BOT-13 | P1: MCP — info_cultura | Execute | Verified |
| BOT-14 | P1: MCP — cultura desconhecida | Execute | Verified |
| BOT-15 | P1: Conversa — /start | Execute | Verified |
| BOT-16 | P1: Conversa — /start id | Execute | Verified |
| BOT-17 | P1: Conversa — id inválido | Execute | Verified |
| BOT-18 | P1: Conversa — localização | Execute | Verified |
| BOT-19 | P1: Conversa — pergunta via Groq + MCP | Execute | Verified |
| BOT-20 | P1: Conversa — prompt do sistema | Execute | Verified |
| BOT-21 | P1: Conversa — sem fazenda | Execute | Verified |
| BOT-22 | P1: Conversa — idioma | Design | Pending |
| BOT-23 | P1: Conversa — memória de 6 | Execute | Verified |
| BOT-24 | P1: Conversa — limite 20/h | Design | Pending |
| BOT-25 | P1: Conversa — falha da Groq | Execute | Verified |
| BOT-26 | P1: Conversa — plano B local | Design | Pending |
| BOT-27 | P2: Fotos — salvar | Design | Pending |
| BOT-28 | P2: Fotos — descrever | Design | Pending |
| BOT-29 | P2: Fotos — registrar | Design | Pending |
| BOT-30 | P2: Fotos — situação hídrica | Design | Pending |
| BOT-31 | P2: Fotos — confirme no campo | Design | Pending |
| BOT-32 | P2: Fotos — sem fazenda | Design | Pending |
| BOT-33 | P2: Alertas — inscrever | Execute | Verified |
| BOT-34 | P2: Alertas — entrada inválida | Execute | Verified |
| BOT-35 | P2: Alertas — 10:00 UTC | Design | Pending |
| BOT-36 | P2: Alertas — balanço desde o plantio | Execute | Verified |
| BOT-37 | P2: Alertas — regra de envio | Execute | Implementing |
| BOT-38 | P2: Alertas — 7 dias | Execute | Implementing |
| BOT-39 | P2: Alertas — série recente | Execute | Verified |
| BOT-40 | P2: Alertas — /testar_alerta | Execute | Verified |
| BOT-41 | P2: Áudio — transcrever | Design | Pending |
| BOT-42 | P2: Áudio — falha | Design | Pending |
| BOT-43 | Edge: variáveis ausentes | Design | Pending |
| BOT-44 | Edge: localização fora de terra | Execute | Verified |
| BOT-45 | Edge: resposta > 4096 | Execute | Verified |
| BOT-46 | Edge: aviso de parâmetro preliminar (motor MOT-63) | Execute | Verified |

**Coverage:** 46 total, 0 mapped to tasks, 45 unmapped ⚠️ (tasks come after approval)

---

## Implicit-requirement dimensions

| Dimension | Covered by |
| --------- | ---------- |
| Input validation & bounds | BOT-14, BOT-17, BOT-34, BOT-44, BOT-45 |
| Failure / partial-failure states | BOT-12, BOT-25, BOT-42, BOT-43 |
| Idempotency / retry / duplicate handling | BOT-18 (uma fazenda por chat), BOT-38 (sem alerta repetido) |
| Auth boundaries & rate limits | BOT-11 (token do MCP), BOT-24 (20/h); bot público por decisão do usuário |
| Concurrency / ordering | BOT-07 |
| Data lifecycle / expiry | BOT-08 + retenção manual até o fim do evento (decisão do usuário) |
| Observability | N/A because errors reach the user as messages (BOT-25, BOT-42) and the motor logs its data requests (MOT-13); no metrics in the MVP |
| External-dependency failure | BOT-25 (Groq), BOT-26 (plano B do Remote MCP), BOT-42 (áudio) |
| State-transition integrity | BOT-21, BOT-32 (sem fazenda → pede localização antes de qualquer ação) |

---

## Sources

- `.specs/STATE.md` AD-001, AD-002, AD-004.
- `.specs/features/motor/spec.md` e `.specs/features/site/spec.md` (SITE-32..36 usam o banco).
- Groq: [Remote MCP](https://console.groq.com/docs/tool-use/remote-mcp), [Responses API](https://console.groq.com/docs/responses-api) — beta; campos exatos a confirmar na implementação.

---

## Success Criteria

- [ ] Demo: pergunta no celular de um jurado e resposta com números do motor.
- [ ] Foto no Telegram vira pin no site após "Atualizar fotos".
- [ ] MCP sem token responde 401.
