# Bot Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/bot/design.md`
**Status**: Approved
**Approved**: 2026-11-14 - user: "aprovado"
**Build**: `.venv/bin/python -m compileall -q core web bot_logica app.py mcp_server.py bot.py; .venv/bin/ruff check .`
**Run bot**: `.venv/bin/python -m pytest -v tests/bot`

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: none - strong defaults applied. pytest set by the motor feature; organization chosen by the user: "2 processos + lógica pura (Recommended)".

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Banco e clima recente (`core/db.py`, `core/recente.py`, `core/alertas.py`) | unit (SQLite em pasta temporária, rede simulada) | Caminho feliz + erro + concorrência entre processos | `tests/bot/test_<modulo>.py` | `.venv/bin/python -m pytest -v tests/bot` |
| Regras do bot (`bot_logica/*.py`) | unit (LLM, motor, banco e Telegram falsos) | Todos os ramos; 1:1 com os ACs; edge cases | `tests/bot/test_<modulo>.py` | `.venv/bin/python -m pytest -v tests/bot` |
| Servidor MCP (`mcp_server.py`) | integration (`starlette.testclient.TestClient`) | Listagem, chamada com token, 401 sem token | `tests/bot/test_mcp_server.py` | `.venv/bin/python -m pytest -v tests/bot` |
| Ligação Telegram (`bot.py`) | unit (`verificar_ambiente`, `agendar` com JobQueue falso) | Ambiente e agendamento | `tests/bot/test_bot.py` | `.venv/bin/python -m pytest -v tests/bot` |
| `.env.example` | none | - (build gate only) | - | build gate only |

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Tarefas com testes | `.venv/bin/python -m pytest -v tests/bot` |
| Full | Tarefa do servidor MCP | `.venv/bin/python -m pytest -v tests/bot` |
| Build | Fim de fase e tarefas sem teste | `.venv/bin/python -m compileall -q core web bot_logica app.py mcp_server.py bot.py; .venv/bin/ruff check .; .venv/bin/python -m pytest -v tests/bot` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Dados

```
T1
T2
T3
```

### Phase 2: Alertas e ferramentas

```
T2 → T4
T3 → T4
T2 → T5
T5 → T6
T1 → T6
```

### Phase 3: LLM e regras de conversa

```
T7
T8
T7 → T9
T9 → T10
T5 → T10
```

### Phase 4: Fluxos

```
T2 → T11
T4 → T11
T7 → T11
T8 → T11
T9 → T11
T11 → T12
T11 → T13
```

### Phase 5: Ligação com o Telegram

```
T11 → T14
T12 → T14
T13 → T14
T4 → T14
```

---

## Task Breakdown

### T1: Variáveis novas no `.env.example`

**What**: Acrescentar `MCP_TOKEN=`, `MCP_PORT=8000`, `DB_PATH=db.sqlite`, `TELEGRAM_BOT_USERNAME=`.
**Where**: `.env.example`
**Depends on**: None
**Reuses**: `.env.example` existente
**Requirement**: BOT-11, BOT-43

**Done when**:

- [ ] Variáveis listadas com comentário curto
- [ ] Gate build passa

**Tests**: none
**Gate**: build

---

### T2: Banco compartilhado

**What**: `core/db.py` com o esquema do design e as funções de fazendas, observações e alertas; uma conexão por operação; caminho por `DB_PATH`.
**Where**: `core/db.py`
**Depends on**: None
**Reuses**: `sqlite3`
**Requirement**: BOT-01, BOT-02, BOT-03, BOT-04, BOT-05, BOT-06, BOT-07, BOT-08

**Done when**:

- [ ] Teste com 2 processos (`multiprocessing`) gravando no mesmo arquivo
- [ ] Gate quick passa; 8 testes

**Tests**: unit
**Gate**: quick

---

### T3: Clima recente

**What**: `core/recente.py` com os últimos 45 dias do POWER, mesmas colunas de `power.serie`, cache de 1 dia.
**Where**: `core/recente.py`
**Depends on**: None
**Reuses**: `core/power.py` (conversão), `core/cache.py`
**Requirement**: BOT-39

**Done when**:

- [ ] Rede simulada; 2ª chamada no mesmo dia não chama a API; no dia seguinte chama
- [ ] Gate quick passa; 1 teste

**Tests**: unit
**Gate**: quick

---

### T4: Verificação de alertas e situação hídrica

**What**: `core/alertas.py` com `situacao` e `verificar` (balanço desde o plantio, Ks < 0,7 e ≤ 15 dias do meio, 7 dias entre envios, `forcar`).
**Where**: `core/alertas.py`
**Depends on**: T2, T3
**Reuses**: `core/balanco.py` (motor T10), `core/culturas.py`, `core/solo.py`
**Requirement**: BOT-36, BOT-37, BOT-38

**Pré-requisito**: motor T10 (`core/balanco.py`). Até lá, os testes injetam um balanço falso.

**Done when**:

- [ ] Gate quick passa; 3 testes

**Tests**: unit
**Gate**: quick

---

### T5: Ferramentas do motor

**What**: `bot_logica/ferramentas.py` com as 8 ferramentas (função, descrição PT/EN, schema JSON) e `executar` com erro legível.
**Where**: `bot_logica/ferramentas.py`
**Depends on**: T2
**Reuses**: `core/*` (injetável), `core/culturas.py`
**Requirement**: BOT-10, BOT-12, BOT-13, BOT-14, BOT-46

**Done when**:

- [ ] Motor falso nos testes
- [ ] Resultado com `preliminar = true` ganha `aviso` (BOT-46)
- [ ] Gate quick passa; 5 testes

**Tests**: unit
**Gate**: quick

---

### T6: Servidor MCP com token

**What**: `mcp_server.py` com `MCPServer` (mcp 2.3), as 8 ferramentas de T5, `streamable_http_app()` atrás de middleware `Authorization: Bearer <MCP_TOKEN>`, `main()` com uvicorn.
**Where**: `mcp_server.py`
**Depends on**: T5, T1
**Reuses**: `bot_logica/ferramentas.py`
**Requirement**: BOT-09, BOT-11

**Done when**:

- [ ] `TestClient` lista as 8 ferramentas com token e recebe 401 sem token e com token errado
- [ ] Gate full passa; 2 testes

**Tests**: integration
**Gate**: full

---

### T7: Idioma e textos do bot

**What**: `bot_logica/idioma.py`: `idioma(language_code)` (pt*/en*/es*, outro → en) e textos fixos do bot em pt/en/es (os da spec + tom da Cecilia).
**Where**: `bot_logica/idioma.py`
**Depends on**: None
**Reuses**: padrão de `core/textos.py`
**Requirement**: BOT-22

**Done when**:

- [ ] Gate quick passa; 1 teste

**Tests**: unit
**Gate**: quick

---

### T8: Limite de 20 mensagens por hora

**What**: `bot_logica/limite.py` com janela móvel de 60 min por chat e relógio injetável.
**Where**: `bot_logica/limite.py`
**Depends on**: None
**Reuses**: -
**Requirement**: BOT-24

**Done when**:

- [ ] 20 permitidas, a 21ª negada, liberada após 60 min
- [ ] Gate quick passa; 1 teste

**Tests**: unit
**Gate**: quick

---

### T9: Assistente Groq com Remote MCP

**What**: `bot_logica/llm.py`: `prompt_sistema`, `Memoria(6)`, `Assistente.responder` pela Responses API com ferramenta `mcp` (URL + cabeçalho do token), timeout 30 s, `LLMIndisponivel` em falha.
**Where**: `bot_logica/llm.py`
**Depends on**: T7
**Reuses**: SDK `openai` com `base_url` da Groq
**Requirement**: BOT-19, BOT-20, BOT-23, BOT-25

**Primeiro passo**: conferir na doc atual da Groq (Remote MCP, beta) os nomes dos campos da ferramenta `mcp` e anotar no design.

**Done when**:

- [ ] Cliente falso registra a requisição; testes conferem modelo, ferramenta `mcp`, URL, cabeçalho, prompt e memória
- [ ] Gate quick passa; 4 testes

**Tests**: unit
**Gate**: quick

---

### T10: Plano B por function calling local

**What**: Em `Assistente`, com `remoto=False`: Chat Completions com os schemas de `FERRAMENTAS`, execução local de cada chamada, máximo de 5 chamadas por mensagem.
**Where**: `bot_logica/llm.py` (modify)
**Depends on**: T9, T5
**Reuses**: `bot_logica/ferramentas.py`
**Requirement**: BOT-26

**Done when**:

- [ ] Gate quick passa; 1 teste novo (5 em `test_llm.py`)

**Tests**: unit
**Gate**: quick

---

### T11: Conversa: start, localização, texto e alertas

**What**: `bot_logica/conversa.py` com `start` (com e sem id), `localizacao`, `texto`, `alerta`, `testar_alerta`, `dividir`; limite, sem fazenda e fora de terra.
**Where**: `bot_logica/conversa.py`
**Depends on**: T2, T4, T7, T8, T9
**Reuses**: `core/db.py`, `core/alertas.py`, `bot_logica/*`
**Requirement**: BOT-15, BOT-16, BOT-17, BOT-18, BOT-21, BOT-33, BOT-34, BOT-40, BOT-44, BOT-45

**Done when**:

- [ ] Banco em pasta temporária; motor e assistente falsos
- [ ] Gate quick passa; 10 testes

**Tests**: unit
**Gate**: quick

---

### T12: Fotos

**What**: `bot_logica/fotos.py` com `tratar_foto`: salvar, descrever (visão, sem diagnóstico), registrar, situação hídrica se houver alerta, frase final, sem fazenda.
**Where**: `bot_logica/fotos.py`
**Depends on**: T11
**Reuses**: `core/db.py`, `core/alertas.situacao`
**Requirement**: BOT-27, BOT-28, BOT-29, BOT-30, BOT-31, BOT-32

**Done when**:

- [ ] Gate quick passa; 6 testes

**Tests**: unit
**Gate**: quick

---

### T13: Áudio

**What**: `bot_logica/audio.py` com `tratar_voz`: transcrever (Whisper da Groq, injetado) e repassar para `Conversa.texto`; falha ou vazio → mensagem.
**Where**: `bot_logica/audio.py`
**Depends on**: T11
**Reuses**: `bot_logica/conversa.py`
**Requirement**: BOT-41, BOT-42

**Done when**:

- [ ] Gate quick passa; 2 testes

**Tests**: unit
**Gate**: quick

---

### T14: Ligação com o Telegram

**What**: `bot.py` com `verificar_ambiente`, handlers (comandos, localização, texto, foto, voz) chamando `bot_logica`, `agendar` às 10:00 UTC e `main()`.
**Where**: `bot.py`
**Depends on**: T11, T12, T13, T4
**Reuses**: python-telegram-bot 22.8, `bot_logica/*`, `core/alertas.verificar`
**Requirement**: BOT-35, BOT-43

**Done when**:

- [ ] Gate quick passa; 2 testes

**Tests**: unit
**Gate**: quick

---

## Checks

**C1** - `criar_fazenda` grava no `db.sqlite` e devolve um id inteiro (BOT-01, Banco AC 1)
Proof: run bot | test_db.py::test_criar_fazenda_retorna_id PASSED

**C2** - `fazenda_por_chat` devolve id, lat, lon e pais da fazenda do chat, ou None sem fazenda (BOT-02, Banco AC 2)
Proof: run bot | test_db.py::test_fazenda_por_chat PASSED

**C3** - `vincular_chat` torna a fazenda a fazenda do chat (BOT-03, Banco AC 3)
Proof: run bot | test_db.py::test_vincular_chat PASSED

**C4** - `salvar_observacao` grava com timestamp UTC e `listar_observacoes` devolve a observação com lat e lon da fazenda (BOT-04, Banco AC 4)
Proof: run bot | test_db.py::test_salvar_e_listar_observacao PASSED

**C5** - `inscrever_alerta` grava uma inscrição ativa e `listar_alertas` a devolve (BOT-05, Banco AC 5)
Proof: run bot | test_db.py::test_inscrever_e_listar_alerta PASSED

**C6** - O arquivo e as tabelas são criados no primeiro uso (BOT-06, Banco AC 6)
Proof: run bot | test_db.py::test_cria_tabelas_no_primeiro_uso PASSED

**C7** - Dois processos usam o mesmo arquivo ao mesmo tempo sem erro nem perda de registros (BOT-07, Banco AC 7)
Proof: run bot | test_db.py::test_dois_processos_mesmo_arquivo PASSED

**C8** - Depois das operações de fazenda, observação e foto, só existem dados em `db.sqlite` e `data/fotos/` (BOT-08, Banco AC 8)
Proof: run bot | test_db.py::test_dados_so_em_db_e_fotos PASSED

**C9** - O MCP lista as 8 ferramentas, cada uma com descrição em PT e EN (BOT-09, MCP AC 1)
Proof: run bot | test_mcp_server.py::test_lista_8_ferramentas_com_descricao PASSED

**C10** - Cada ferramenta devolve o resultado do motor para os argumentos, com `fontes` quando o motor as devolve (BOT-10, MCP AC 2)
Proof: run bot | test_ferramentas.py::test_resultado_do_motor_com_fontes PASSED

**C11** - Sem `Authorization: Bearer <MCP_TOKEN>`, ou com outro token, a resposta é HTTP 401 e nenhuma ferramenta roda (BOT-11, MCP AC 3)
Proof: run bot | test_mcp_server.py::test_sem_token_401 PASSED

**C12** - `ErroPontoInvalido`, `ErroFonteDados` e `ValueError` viram resultado de erro com a mensagem e sem stack trace (BOT-12, MCP AC 4)
Proof: run bot | test_ferramentas.py::test_erros_legiveis_sem_stacktrace PASSED

**C13** - `info_cultura` devolve papel, familia, fixa_n, climas, tolerancia_seca, efeito_solo e fonte (BOT-13, MCP AC 5)
Proof: run bot | test_ferramentas.py::test_info_cultura PASSED

**C14** - `info_cultura` com cultura desconhecida devolve erro listando as culturas conhecidas (BOT-14, MCP AC 6)
Proof: run bot | test_ferramentas.py::test_info_cultura_desconhecida PASSED

**C15** - `/start` responde com boas-vindas, pede a localização e avisa que fotos e localização ficam guardadas até o fim do evento (BOT-15, Conversa AC 1)
Proof: run bot | test_conversa.py::test_start_boas_vindas_privacidade PASSED

**C16** - `/start <id>` existente vincula a fazenda ao chat e responde com o resumo do clima dela (BOT-16, Conversa AC 2)
Proof: run bot | test_conversa.py::test_start_id_vincula_fazenda PASSED

**C17** - `/start <id>` inexistente responde "Não encontrei essa fazenda. Mande sua localização." e não vincula nada (BOT-17, Conversa AC 3)
Proof: run bot | test_conversa.py::test_start_id_inexistente PASSED

**C18** - Localização cria ou atualiza a fazenda do chat e responde com o resumo do clima, o 1º item do ranking de hoje e "Dados: NASA POWER" (BOT-18, Conversa AC 4)
Proof: run bot | test_conversa.py::test_localizacao_resumo_e_melhor_cultura PASSED

**C19** - Pergunta com fazenda vai à Responses API da Groq com a ferramenta `mcp` apontando para `MCP_PUBLIC_URL` com o cabeçalho do token, e a resposta é o texto final do modelo (BOT-19, Conversa AC 5)
Proof: run bot | test_llm.py::test_pergunta_usa_responses_com_remote_mcp PASSED

**C20** - O prompt do sistema tem lat, lon e id da fazenda, o idioma, a regra "Todo número deve vir de uma ferramenta; nunca invente valores" e o pedido de citar as fontes (BOT-20, Conversa AC 6)
Proof: run bot | test_llm.py::test_prompt_sistema_regras PASSED

**C21** - Pergunta sem fazenda pede a localização e não chama o modelo (BOT-21, Conversa AC 7)
Proof: run bot | test_conversa.py::test_pergunta_sem_fazenda_pede_localizacao PASSED

**C22** - `language_code` pt*/en*/es* vira pt/en/es, e qualquer outro vira en (BOT-22, Conversa AC 8)
Proof: run bot | test_idioma.py::test_language_code_para_idioma PASSED

**C23** - O modelo recebe as últimas 6 mensagens do chat como contexto (BOT-23, Conversa AC 9)
Proof: run bot | test_llm.py::test_memoria_ultimas_6 PASSED

**C24** - Com 20 mensagens nos últimos 60 min, a 21ª recebe "Você atingiu o limite de 20 mensagens por hora. Tente de novo mais tarde." e não é processada (BOT-24, Conversa AC 10)
Proof: run bot | test_limite.py::test_limite_20_por_hora PASSED

**C25** - Falha, timeout de 30 s ou limite da Groq geram "O assistente está indisponível agora. Tente de novo em alguns minutos." (BOT-25, Conversa AC 11)
Proof: run bot | test_llm.py::test_falha_groq_mensagem_erro PASSED

**C26** - Com `USE_REMOTE_MCP=false`, Chat Completions com as ferramentas como funções, execução local e no máximo 5 chamadas por mensagem (BOT-26, Conversa AC 12)
Proof: run bot | test_llm.py::test_plano_b_local_max_5_ferramentas PASSED

**C27** - A foto é salva na maior resolução em `data/fotos/<fazenda_id>_<timestamp>.jpg` (BOT-27, Fotos AC 1)
Proof: run bot | test_fotos.py::test_salva_maior_foto PASSED

**C28** - A foto vai ao modelo de visão com a instrução de descrever cultura, cor das folhas, murcha e solo exposto, sem diagnóstico (BOT-28, Fotos AC 2)
Proof: run bot | test_fotos.py::test_descricao_sem_diagnostico PASSED

**C29** - A observação é gravada com a legenda (ou texto vazio) e a descrição (BOT-29, Fotos AC 3)
Proof: run bot | test_fotos.py::test_registra_observacao PASSED

**C30** - Com alerta ativo, a resposta da foto inclui a situação hídrica atual da cultura (BOT-30, Fotos AC 4)
Proof: run bot | test_fotos.py::test_situacao_hidrica_com_alerta PASSED

**C31** - Toda resposta de foto termina com "Confirme no campo: pode ser falta d'água, praga, doença ou compactação." (BOT-31, Fotos AC 5)
Proof: run bot | test_fotos.py::test_termina_com_confirme_no_campo PASSED

**C32** - Foto sem fazenda pede a localização e não salva a foto (BOT-32, Fotos AC 6)
Proof: run bot | test_fotos.py::test_foto_sem_fazenda PASSED

**C33** - `/alerta <cultura> <DD/MM/AAAA>` inscreve a fazenda e confirma (BOT-33, Alertas AC 1)
Proof: run bot | test_conversa.py::test_alerta_inscreve PASSED

**C34** - Cultura desconhecida ou data inválida respondem com as culturas e o formato "/alerta Milho 15/02/2026" sem inscrever (BOT-34, Alertas AC 2)
Proof: run bot | test_conversa.py::test_alerta_entrada_invalida PASSED

**C35** - A verificação de alertas é agendada uma vez por dia às 10:00 UTC (BOT-35, Alertas AC 3)
Proof: run bot | test_bot.py::test_job_diario_10_utc PASSED

**C36** - A verificação calcula o balanço desde a data de plantio até o último dia do POWER com a série recente (BOT-36, Alertas AC 4)
Proof: run bot | test_alertas.py::test_balanco_desde_plantio PASSED

**C37** - Com Ks < 0,7 e fase de meio em ≤ 15 dias, o alerta vai para o chat da fazenda e diz que os dados da NASA têm atraso de alguns dias (BOT-37, Alertas AC 5)
Proof: run bot | test_alertas.py::test_envia_quando_ks_baixo_perto_do_florescimento PASSED

**C38** - Fazenda que recebeu alerta nos últimos 7 dias não recebe outro (BOT-38, Alertas AC 6)
Proof: run bot | test_alertas.py::test_nao_repete_em_7_dias PASSED

**C39** - `recente.serie(lat, lon, 45)` devolve os últimos 45 dias com as colunas de `power.serie`, com cache de 1 dia (BOT-39, Alertas AC 7)
Proof: run bot | test_recente.py::test_ultimos_45_dias_cache_1_dia PASSED

**C40** - `/testar_alerta` roda a verificação do chat na hora, ignorando a regra dos 7 dias (BOT-40, Alertas AC 8)
Proof: run bot | test_conversa.py::test_testar_alerta_ignora_7_dias PASSED

**C41** - Mensagem de voz é transcrita pelo modelo de áudio e tratada como pergunta de texto (BOT-41, Áudio AC 1)
Proof: run bot | test_audio.py::test_transcreve_e_processa PASSED

**C42** - Transcrição com falha ou vazia responde "Não consegui entender o áudio. Pode escrever ou mandar de novo?" (BOT-42, Áudio AC 2)
Proof: run bot | test_audio.py::test_falha_transcricao PASSED

**C43** - Sem `MCP_TOKEN`, `GROQ_API_KEY` ou `TELEGRAM_BOT_TOKEN`, o processo sai com mensagem nomeando a variável (BOT-43, Edge 1)
Proof: run bot | test_bot.py::test_variaveis_ausentes PASSED

**C44** - Localização fora de terra responde "Esse ponto fica fora de terra firme. Mande outra localização." e mantém a fazenda anterior (BOT-44, Edge 2)
Proof: run bot | test_conversa.py::test_localizacao_fora_de_terra PASSED

**C45** - Resposta com mais de 4096 caracteres é dividida em várias mensagens (BOT-45, Edge 3)
Proof: run bot | test_conversa.py::test_divide_mensagem_4096 PASSED

**C46** - Resultado de ferramenta com item `preliminar = true` inclui `aviso` "parâmetros genéricos da FAO, não calibrados para a região" no idioma do usuário (BOT-46, Edge 4)
Proof: run bot | test_ferramentas.py::test_aviso_preliminar PASSED

---

## Handoff

The feature's live state, written as it happens - a compaction gives no warning.

**Settled mid-build:** none
**Dispatched:** none
**Walked:** none

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

Phase 1:  T1, T2, T3            (env, banco, clima recente)
Phase 2:  T4, T5, T6            (alertas, ferramentas, servidor MCP)
Phase 3:  T7, T8, T9, T10       (idioma, limite, Groq, plano B)
Phase 4:  T11, T12, T13         (conversa, fotos, áudio)
Phase 5:  T14                   (bot.py)
```

Execution is strictly sequential - there is no intra-phase parallelism.
