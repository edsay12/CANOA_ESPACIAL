# Site Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/site/design.md`
**Status**: Approved
**Approved**: 2026-11-14 - user: "aprovo"
**Build**: `.venv/bin/python -m compileall -q core web app.py mcp_server.py bot.py; .venv/bin/ruff check .`
**Run web**: `.venv/bin/python -m pytest -v tests/web`
**Run app**: `.venv/bin/python -m pytest -v tests/app`

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: none - strong defaults applied. Test approach chosen by the user: "app.py fino + módulos puros (Recommended)"; pytest already set by the motor feature.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Regras de exibição (`web/*.py`) | unit | Todos os ramos; 1:1 com os ACs; todo edge case listado | `tests/web/test_<modulo>.py` | `.venv/bin/python -m pytest -v tests/web` |
| Tela (`app.py`) | integration (Streamlit `AppTest`, motor e banco falsos) | Todo gesto da spec: estado inicial, ação, o que aparece depois; caminhos de erro | `tests/app/test_app.py` | `.venv/bin/python -m pytest -v tests/app` |
| Clique no mapa real, layout 390 px, mensagem de carregando | walk | Visita no navegador | - | walk |

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Tarefas de `web/` | `.venv/bin/python -m pytest -v tests/web` |
| Full | Tarefas de `app.py` | `.venv/bin/python -m pytest -v tests/web tests/app` |
| Build | Fim de fase | `.venv/bin/python -m compileall -q core web app.py mcp_server.py bot.py; .venv/bin/ruff check .; .venv/bin/python -m pytest -v tests/web tests/app` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Base

```
T1
T2
T3
```

### Phase 2: Apresentação

```
T1 → T4
T1 → T5
T1 → T6
T1 → T7
```

### Phase 3: Tela

```
T1 → T8
T2 → T8
T3 → T8
T8 → T9
T4 → T9
T9 → T10
T5 → T10
T10 → T11
T6 → T11
T11 → T12
```

### Phase 4: Interligação com o bot

```
T12 → T13
T7 → T13
T3 → T13
```

---

## Task Breakdown

### T1: Textos da interface em pt/en/es

**What**: `IDIOMAS`, `t(chave, idioma)` e todas as chaves fixas da spec (mensagens de estado, rótulos, abas, limites), com idioma desconhecido → pt.
**Where**: `web/i18n.py`
**Depends on**: None
**Reuses**: padrão de `core/textos.py`
**Requirement**: SITE-27, SITE-30

**Done when**:

- [ ] Toda chave existe nos 3 idiomas (teste percorre as chaves)
- [ ] Texto de limites contém os 4 itens de SITE-30
- [ ] Gate quick passa; 3 testes

**Tests**: unit
**Gate**: quick

---

### T2: Pontos da demo e normalização do clique

**What**: `DEMO` com os 4 rótulos e coordenadas; `normalizar(lat, lon)` com 2 casas e longitude em [-180, 180].
**Where**: `web/pontos.py`
**Depends on**: None
**Reuses**: coordenadas do motor context.md
**Requirement**: SITE-03, SITE-37

**Done when**:

- [ ] `normalizar(-17.8049, -50.9183) == (-17.8, -50.92)`; `normalizar(10, 190) == (10.0, -170.0)`
- [ ] Gate quick passa; 3 testes

**Tests**: unit
**Gate**: quick

---

### T3: Serviço com reuso na sessão

**What**: `Servico(motor, db, memoria)` com `contexto`, `clima`, `ranking`, `planos`, `fazenda`, `observacoes`, `db_disponivel`; mesma chamada → mesmo resultado sem chamar o motor de novo; fazenda reusada por ponto.
**Where**: `web/servico.py`
**Depends on**: None
**Reuses**: contratos do motor
**Requirement**: SITE-09, SITE-36

**Done when**:

- [ ] Motor falso conta chamadas; 2ª chamada igual não chama
- [ ] `fazenda` 2× no mesmo ponto devolve o mesmo id e chama `criar_fazenda` 1×
- [ ] Gate quick passa; 3 testes

**Tests**: unit
**Gate**: quick

---

### T4: Apresentação do clima

**What**: `cards_clima`, `dados_grafico`, `aviso_anos_sem_estacao`, incluindo o modo anual.
**Where**: `web/apresentacao.py`
**Depends on**: T1
**Reuses**: `web.i18n`
**Requirement**: SITE-11, SITE-12, SITE-13, SITE-14

**Done when**:

- [ ] 5 cartões com antes, depois e diferença; modo anual com 2 cartões e a nota
- [ ] `dados_grafico` tem 31 linhas e coluna `periodo` "1995–2009"/"2010–2025"
- [ ] Gate quick passa; 4 testes

**Tests**: unit
**Gate**: quick

---

### T5: Apresentação do ranking

**What**: `cards_ranking` (ordem do motor, campos, retorno ou "sem dado") e `prioridades_vazias`.
**Where**: `web/apresentacao.py` (modify)
**Depends on**: T1
**Reuses**: `web.i18n`
**Requirement**: SITE-17, SITE-18, SITE-20

**Done when**:

- [ ] Gate quick passa; 3 testes novos

**Tests**: unit
**Gate**: quick

---

### T6: Apresentação dos planos

**What**: `cards_planos` com o plano atual primeiro e os campos de cada plano.
**Where**: `web/apresentacao.py` (modify)
**Depends on**: T1
**Reuses**: `web.i18n`
**Requirement**: SITE-25, SITE-26

**Done when**:

- [ ] Gate quick passa; 2 testes novos

**Tests**: unit
**Gate**: quick

---

### T7: Apresentação das observações e erros

**What**: `marcadores(obs)`, `popup(obs)`, `selo(nivel, idioma)` e `mensagem_erro(exc, idioma)`.
**Where**: `web/apresentacao.py` (modify)
**Depends on**: T1
**Reuses**: `core.erros`
**Requirement**: SITE-05, SITE-07, SITE-08, SITE-32, SITE-33

**Done when**:

- [ ] Gate quick passa; 4 testes novos

**Tests**: unit
**Gate**: quick

---

### T8: Tela base: abertura, ponto, contexto, erros e idioma

**What**: `app.py` com seletor de idioma, mapa, 4 botões da demo, mensagem inicial, faixa de contexto (país, coordenadas, selo), estados de erro e de carregando.
**Where**: `app.py`
**Depends on**: T1, T2, T3
**Reuses**: `web.*`
**Requirement**: SITE-01, SITE-02, SITE-04, SITE-05, SITE-06, SITE-07, SITE-08, SITE-27, SITE-28

**Done when**:

- [ ] `tests/app/test_app.py` com motor falso injetado
- [ ] Gate full passa; 8 testes em `tests/app`

**Tests**: integration
**Gate**: full

---

### T9: Aba "Seu clima mudou"

**What**: Resumo primeiro, cartões, gráfico e aviso; erro na aba não derruba as outras.
**Where**: `app.py` (modify)
**Depends on**: T8, T4
**Reuses**: `web.apresentacao` clima
**Requirement**: SITE-10, SITE-40

**Done when**:

- [ ] Gate full passa; 2 testes novos em `tests/app`

**Tests**: integration
**Gate**: full

---

### T10: Aba "O que plantar"

**What**: Data (03-01), 3 sliders (40/40/20), recálculo ao mudar, cartões, culturas ignoradas, prioridades zeradas, ranking vazio, ValueError junto ao controle.
**Where**: `app.py` (modify)
**Depends on**: T9, T5
**Reuses**: `web.apresentacao` ranking
**Requirement**: SITE-15, SITE-16, SITE-19, SITE-20, SITE-21, SITE-39

**Done when**:

- [ ] Gate full passa; 6 testes novos em `tests/app`

**Tests**: integration
**Gate**: full

---

### T11: Aba "Planos de rotação"

**What**: 3 seletores com as candidatas, pedido de histórico, chamada com `historico`, cartões com o atual primeiro.
**Where**: `app.py` (modify)
**Depends on**: T10, T6
**Reuses**: `web.apresentacao` planos
**Requirement**: SITE-22, SITE-23, SITE-24

**Done when**:

- [ ] Gate full passa; 3 testes novos em `tests/app`

**Tests**: integration
**Gate**: full

---

### T12: Painel "Por que confiar"

**What**: Expander com `fontes`, texto de limites e link do NASA POWER.
**Where**: `app.py` (modify)
**Depends on**: T11
**Reuses**: `web.i18n` limites
**Requirement**: SITE-29, SITE-30, SITE-31

**Done when**:

- [ ] Gate full passa; 2 testes novos em `tests/app`

**Tests**: integration
**Gate**: full

---

### T13: Fotos no mapa e botão do Telegram

**What**: Marcadores das observações, popup, "Atualizar fotos", "Receber alertas no Telegram" (cria fazenda, abre `t.me/<bot>?start=<id>`, reusa id); tudo escondido sem `core/db.py`.
**Where**: `app.py` (modify)
**Depends on**: T12, T7, T3
**Reuses**: `web.servico`, `web.apresentacao` observações
**Requirement**: SITE-32, SITE-33, SITE-34, SITE-35, SITE-36

**Pré-requisito externo**: `core/db.py` com `criar_fazenda` e `listar_observacoes` (feature 3). Até lá, os testes usam banco falso e a tela real esconde os recursos.

**Done when**:

- [ ] Gate full passa; 3 testes novos em `tests/app`

**Tests**: integration
**Gate**: full

---

## Checks

**C1** - Ao abrir: mapa-múndi sem ponto, "Clique no mapa ou escolha um exemplo" e os botões "Rio Verde (BR)", "Nakuru (KE)", "Ludhiana (IN)", "Ames (US)" (SITE-01, Ponto AC 1)
Proof: run app | test_app.py::test_abertura_mapa_mensagem_botoes PASSED

**C2** - Sem ponto selecionado, nenhuma aba de resultado aparece (SITE-02, Ponto AC 2)
Proof: run app | test_app.py::test_sem_ponto_sem_abas PASSED

**C3** - O clique no mapa vira um ponto com lat/lon arredondados a 2 casas (SITE-03, Ponto AC 3)
Proof: run web | test_pontos.py::test_clique_arredonda_2_casas PASSED

**C4** - Clicar num botão da demo seleciona as coordenadas daquele ponto (SITE-04, Ponto AC 4)
Proof: run app | test_app.py::test_botao_demo_seleciona_ponto PASSED

**C5** - Com ponto: país, coordenadas e o selo "Dados municipais" / "Dados do país" / "Estimado pelo clima" conforme `nivel_precisao` (SITE-05, Ponto AC 5)
Proof: run app | test_app.py::test_ponto_mostra_pais_coordenadas_selo PASSED

**C6** - Enquanto o motor calcula aparece "Calculando com 30 anos de dados da NASA…" (SITE-06, Ponto AC 6)
Proof: walk - selecionar Ludhiana sem cache na sessão mostra "Calculando com 30 anos de dados da NASA…" até as abas aparecerem

**C7** - `ErroPontoInvalido` mostra "Esse ponto fica fora de terra firme. Escolha outro lugar." e nenhuma aba (SITE-07, Ponto AC 7)
Proof: run app | test_app.py::test_fora_de_terra_mensagem PASSED

**C8** - `ErroFonteDados` mostra "Os dados da NASA estão indisponíveis agora. Tente de novo em alguns minutos." e nenhuma aba (SITE-08, Ponto AC 8)
Proof: run app | test_app.py::test_fonte_indisponivel_mensagem PASSED

**C9** - O mesmo ponto com as mesmas entradas na sessão não chama o motor de novo (SITE-09, Ponto AC 9)
Proof: run web | test_servico.py::test_reusa_resultado_na_sessao PASSED

**C10** - A aba "Seu clima mudou" mostra o `resumo` do motor como primeiro texto (SITE-10, Clima AC 1)
Proof: run app | test_app.py::test_clima_resumo_primeiro PASSED

**C11** - 5 cartões (chuva da estação, início, fim, veranicos, dias ≥ 35 °C) com valor 1995–2009, valor 2010–2025 e diferença (SITE-11, Clima AC 2)
Proof: run web | test_apresentacao.py::test_cards_clima_cinco_indicadores PASSED

**C12** - Em `modo = "anual"`: cartões de chuva anual e dias ≥ 35 °C e a nota "Sem estação chuvosa definida: comparando o ano inteiro" (SITE-12, Clima AC 3)
Proof: run web | test_apresentacao.py::test_cards_clima_modo_anual PASSED

**C13** - O gráfico recebe a chuva de cada ano de 1995 a 2025 com os dois períodos marcados (SITE-13, Clima AC 4)
Proof: run web | test_apresentacao.py::test_dados_grafico_chuva_por_ano_periodos PASSED

**C14** - Com `anos_sem_estacao` > 0 aparece "Anos sem estação chuvosa detectada: N" (SITE-14, Clima AC 5)
Proof: run web | test_apresentacao.py::test_aviso_anos_sem_estacao PASSED

**C15** - A aba "O que plantar" tem data de semeadura 03-01 e sliders "Retorno" 40, "Segurança contra seca" 40, "Saúde do solo" 20 (SITE-15, Plantar AC 1)
Proof: run app | test_app.py::test_plantar_controles_padrao PASSED

**C16** - Mudar a data ou um slider chama `ranking_safra` com os novos valores e redesenha o ranking (SITE-16, Plantar AC 2)
Proof: run app | test_app.py::test_plantar_recalcula_ao_mudar PASSED

**C17** - Um cartão por item, na ordem do motor, com nome, nota, "Risco de quebra: N%", anos_quebra, nota_solo e explicação (SITE-17, Plantar AC 3)
Proof: run web | test_apresentacao.py::test_cards_ranking_ordem_e_campos PASSED

**C18** - Retorno aparece com a moeda; sem retorno aparece "Retorno: sem dado" (SITE-18, Plantar AC 4)
Proof: run web | test_apresentacao.py::test_retorno_ou_sem_dado PASSED

**C19** - `culturas_ignoradas` não vazia aparece em "Culturas sem dados suficientes" (SITE-19, Plantar AC 5)
Proof: run app | test_app.py::test_culturas_ignoradas_listadas PASSED

**C20** - Com os 3 sliders em 0 aparece "Escolha pelo menos uma prioridade" e o motor não é chamado (SITE-20, Plantar AC 6)
Proof: run app | test_app.py::test_prioridades_zeradas_nao_chama_motor PASSED

**C21** - `itens` vazio mostra "Nenhuma cultura com dados suficientes para este lugar" (SITE-21, Plantar AC 7)
Proof: run app | test_app.py::test_ranking_vazio_mensagem PASSED

**C22** - A aba "Planos de rotação" tem os seletores "Safra 1", "Safra 2", "Safra 3" com as culturas candidatas do ponto (SITE-22, Planos AC 1)
Proof: run app | test_app.py::test_planos_seletores_candidatas PASSED

**C23** - Com algum seletor vazio aparece "Informe o que você plantou nas últimas 3 safras" e o motor não é chamado (SITE-23, Planos AC 2)
Proof: run app | test_app.py::test_planos_historico_incompleto PASSED

**C24** - Com os 3 seletores preenchidos, `planos_rotacao` é chamado com eles como `historico` e as prioridades atuais (SITE-24, Planos AC 3)
Proof: run app | test_app.py::test_planos_chama_motor_com_historico PASSED

**C25** - O plano atual vem primeiro com "Seu plano atual", seguido dos outros na ordem do motor (SITE-25, Planos AC 4)
Proof: run web | test_apresentacao.py::test_cards_planos_atual_primeiro PASSED

**C26** - Cada plano mostra as 3 culturas em ordem, nota, risco, nota_solo, retorno_ano com moeda (ou "sem dado") e explicação (SITE-26, Planos AC 5)
Proof: run web | test_apresentacao.py::test_cards_planos_campos PASSED

**C27** - O seletor de idioma oferece "Português", "English", "Español", com Português ao abrir (SITE-27, Idioma AC 1)
Proof: run app | test_app.py::test_idioma_padrao_portugues PASSED

**C28** - Escolher English troca todos os textos fixos e passa `idioma="en"` ao motor (SITE-28, Idioma AC 2)
Proof: run app | test_app.py::test_idioma_ingles_troca_textos_e_motor PASSED

**C29** - O painel "Por que confiar" lista todas as `fontes` do motor (SITE-29, Confiar AC 1)
Proof: run app | test_app.py::test_confiar_lista_fontes PASSED

**C30** - O texto de limites cita dados regionais (~50 km), não diagnostica pragas/doenças, janela estimada pelo clima e não considera irrigação (SITE-30, Confiar AC 2)
Proof: run web | test_i18n.py::test_texto_limites PASSED

**C31** - "NASA POWER" no painel aponta para `https://power.larc.nasa.gov/` (SITE-31, Confiar AC 3)
Proof: run app | test_app.py::test_confiar_link_power PASSED

**C32** - Um marcador por observação, diferente do marcador do ponto selecionado (SITE-32, Fotos AC 1)
Proof: run web | test_apresentacao.py::test_marcadores_observacoes PASSED

**C33** - O popup da observação tem data, texto, `descricao_ia` e miniatura da foto (SITE-33, Fotos AC 2)
Proof: run web | test_apresentacao.py::test_popup_observacao_campos PASSED

**C34** - "Atualizar fotos" recarrega as observações do banco (SITE-34, Fotos AC 3)
Proof: run app | test_app.py::test_atualizar_fotos_recarrega PASSED

**C35** - "Receber alertas no Telegram" cria a fazenda do ponto e abre `https://t.me/<bot>?start=<id>` (SITE-35, Fotos AC 4)
Proof: run app | test_app.py::test_telegram_cria_fazenda_e_link PASSED

**C36** - Dois cliques no mesmo ponto e sessão reutilizam o mesmo id de fazenda (SITE-36, Fotos AC 5)
Proof: run web | test_servico.py::test_fazenda_reusada_na_sessao PASSED

**C37** - Longitude fora de [-180, 180] vinda do mapa é normalizada antes de chamar o motor (SITE-37, Edge 1)
Proof: run web | test_pontos.py::test_longitude_normalizada PASSED

**C38** - Em 390 px de largura os cartões ficam numa coluna e a página não rola na horizontal (SITE-38, Edge 2)
Proof: walk - janela de 390 px com Rio Verde selecionado: cartões empilhados, sem barra de rolagem horizontal

**C39** - `ValueError` do motor aparece junto ao controle que o causou (SITE-39, Edge 3)
Proof: run app | test_app.py::test_valueerror_mostra_mensagem_no_controle PASSED

**C40** - Erro do motor numa aba não impede as outras de funcionar (SITE-40, Edge 4)
Proof: run app | test_app.py::test_aba_com_erro_nao_derruba_outras PASSED

---

## Handoff

The feature's live state, written as it happens - a compaction gives no warning.

**Settled mid-build:** none
**Dispatched:** none
**Walked:** none

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4

Phase 1:  T1, T2, T3                (textos, pontos, serviço)
Phase 2:  T4, T5, T6, T7            (apresentação)
Phase 3:  T8, T9, T10, T11, T12     (tela e abas)
Phase 4:  T13                       (fotos e Telegram)
```

Execution is strictly sequential - there is no intra-phase parallelism.
