# Site (Streamlit `app.py`) Specification

**Approved**: 2026-11-14 - user: "faz isso mesmo Recomendo acrescentar à spec do motor um critério novo, MOT-61 ... e aprovo"

## Problem Statement

O motor calcula o risco climático e os planos de rotação, mas o técnico, o produtor e o jurado precisam ver isso em segundos, sem programar. O site é a porta de entrada visual: escolher um lugar no mundo e entender como o clima mudou ali e o que plantar, com as fontes à vista. Ele só exibe o que o motor devolve (AD-001, AD-004).

## Goals

- [ ] Do primeiro clique num ponto da demo até ver as 3 abas preenchidas: menos de 10 s com cache.
- [ ] Funciona em notebook (1366×768) e celular (390 px) sem rolagem horizontal da página.
- [ ] Os 4 pontos da demo mostram resultados diferentes nas 3 abas.

## Out of Scope

| Feature | Reason |
| ------- | ------ |
| Qualquer cálculo agronômico ou climático | Pertence ao motor (AD-004) |
| Login, contas, várias fazendas por usuário | Site público no MVP (decisão do usuário) |
| Banco SQLite, bot e servidor MCP | Feature 3 (bot + MCP) |
| Clima futuro (CMIP6), SMAP/NDVI, PDF | Deferred Ideas |
| Layout definido em pixels | Sem wireframe: a spec define comportamentos; layout é do construtor dentro do Streamlit |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Wireframe | Não existe; spec sem layout | user: "Ainda não existe (Recommended)" | y |
| Abertura | Mapa-múndi, sem ponto, mensagem + 4 botões da demo | user: "Mapa-múndi + 4 botões da demo (Recommended)" | y |
| Larguras-alvo | 1366×768 e 390 px | user: "Notebook e celular (Recommended)" | y |
| Acesso | Público, sem login | user: "Qualquer pessoa, sem login (Recommended)" | y |
| Idiomas | PT (padrão), EN, ES | Herdado da feature motor | y |
| Valores iniciais dos controles | Prioridades 40/40/20; data de semeadura 03-01; histórico vazio | Mesmos padrões do motor; 03-01 é a safrinha típica do Cerrado | n |
| Textos dos estados | Propostos nos critérios; Cecilia pode reescrever mantendo o sentido | Sem wireframe; o tom é da Cecilia | n |
| Clique no mapa | Coordenadas arredondadas a 2 casas, como o cache do motor | Mesmo ponto → mesmo cache | n |
| Histórico vazio na aba Planos | A aba pede o histórico em vez de calcular | O motor exige o plano atual | n |
| Pins e botão do Telegram | Dependem de `core/db.py` da feature 3; ficam P3 aqui | O banco é especificado na feature bot + MCP | n |

**Open questions:** none - all resolved or logged above (required before the spec is confirmed).

---

## User Stories

### P1: Escolher um ponto e ver o contexto ⭐ MVP

**User Story**: As a técnico, produtor ou jurado, I want to pick any place on a world map (or a demo example) so that I see the recommendation for that place.

**Why P1**: Sem ponto não há nada para mostrar; os botões da demo garantem o pitch.

**Acceptance Criteria**:

1. WHEN the site opens THEN the system SHALL show a world map with no point selected, the message "Clique no mapa ou escolha um exemplo" and four buttons: "Rio Verde (BR)", "Nakuru (KE)", "Ludhiana (IN)", "Ames (US)".
2. WHILE no point is selected the system SHALL show no result tabs.
3. WHEN a user clicks a place on the map THEN the system SHALL select that point with latitude and longitude rounded to 2 decimals and mark it on the map.
4. WHEN a user clicks a demo button THEN the system SHALL select that demo point's coordinates and mark it on the map.
5. WHEN a point is selected THEN the system SHALL show the country name, the coordinates and the precision badge for `nivel_precisao`: "Dados municipais" (municipal), "Dados do país" (pais) or "Estimado pelo clima" (clima).
6. WHILE the motor is computing the system SHALL show the message "Calculando com 30 anos de dados da NASA…".
7. IF the motor raises `ErroPontoInvalido` THEN the system SHALL show "Esse ponto fica fora de terra firme. Escolha outro lugar." and no result tabs.
8. IF the motor raises `ErroFonteDados` THEN the system SHALL show "Os dados da NASA estão indisponíveis agora. Tente de novo em alguns minutos." and no result tabs.
9. WHEN the same point and inputs are requested again in the same session THEN the system SHALL reuse the previous result without calling the motor again.

**Independent Test**: Abrir o site, ver mapa + botões; clicar "Nakuru (KE)" e ver país e selo; clicar no oceano e ver a mensagem de fora de terra.

---

### P1: Aba "Seu clima mudou" ⭐ MVP

**User Story**: As a produtor, I want to see how the climate of my place changed since 2010 so that I understand why my rotation may need to change.

**Why P1**: Abre a demo e o pitch com dado da NASA.

**Acceptance Criteria**:

1. WHEN a point is selected THEN the system SHALL show the tab "Seu clima mudou" with the motor's `resumo` as the first text.
2. WHEN `clima_mudou` returns season values THEN the system SHALL show one card per indicator — chuva da estação (mm), início das chuvas, fim das chuvas, veranicos por estação, dias ≥ 35 °C — each with the 1995–2009 value, the 2010–2025 value and the difference.
3. WHEN `clima_mudou` returns `modo = "anual"` THEN the system SHALL show the cards for annual rainfall and days ≥ 35 °C and the note "Sem estação chuvosa definida: comparando o ano inteiro".
4. WHEN a point is selected THEN the system SHALL show a chart of rainfall per year from 1995 to 2025 with the two periods visually distinguished.
5. WHEN `anos_sem_estacao` is greater than 0 THEN the system SHALL show "Anos sem estação chuvosa detectada: N".

**Independent Test**: Selecionar Rio Verde e ver resumo, 5 cards e o gráfico; selecionar Ames e ver o modo anual se o motor o devolver.

---

### P1: Aba "O que plantar" ⭐ MVP

**User Story**: As a produtor, I want to rank the crops for a sowing date according to my priorities so that I choose the next season with less risk.

**Why P1**: É a rede de segurança do MVP: responde ao desafio sozinha.

**Acceptance Criteria**:

1. WHEN a point is selected THEN the system SHALL show the tab "O que plantar" with a sowing-date input (default 03-01) and three priority sliders "Retorno", "Segurança contra seca", "Saúde do solo" (defaults 40, 40, 20).
2. WHEN a user changes the sowing date or a priority slider THEN the system SHALL call `ranking_safra` with the new values and redraw the ranking.
3. The system SHALL show one card per item of `itens`, in the order the motor returns, with the crop name, `nota` (0–100), `risco_pct` as "Risco de quebra: N%", `anos_quebra`, `nota_solo` (1–5) and `explicacao`.
4. WHEN an item has `retorno` THEN the system SHALL show it with its `moeda`; WHEN `retorno` is None THEN the system SHALL show "Retorno: sem dado".
5. WHEN `culturas_ignoradas` is not empty THEN the system SHALL list them under "Culturas sem dados suficientes".
6. IF all three priority sliders are 0 THEN the system SHALL show "Escolha pelo menos uma prioridade" and not call the motor.
7. IF `itens` is empty THEN the system SHALL show "Nenhuma cultura com dados suficientes para este lugar".

**Independent Test**: Rio Verde, data 03-15: ver cards ordenados; mover "Saúde do solo" para 100 e os outros para 0 e ver a ordem mudar.

---

### P2: Aba "Planos de rotação"

**User Story**: As a produtor, I want to compare 3-year rotation plans with what I plant today so that I pick a rotation that protects the soil and survives the new climate.

**Why P2**: É o diferencial do desafio, mas depende do ranking.

**Acceptance Criteria**:

1. WHEN a point is selected THEN the system SHALL show the tab "Planos de rotação" with three selectors "Safra 1", "Safra 2", "Safra 3" listing the point's candidate crops.
2. WHILE any of the three selectors is empty the system SHALL show "Informe o que você plantou nas últimas 3 safras" and not call the motor.
3. WHEN the three selectors are filled THEN the system SHALL call `planos_rotacao` with them as `historico` and the current priorities.
4. The system SHALL show the current plan first, labeled "Seu plano atual", followed by the other plans in the motor's order.
5. The system SHALL show for each plan its 3 crops in order, `nota`, `risco_pct`, `nota_solo`, `retorno_ano` with `moeda` (or "sem dado") and `explicacao`.

**Independent Test**: Rio Verde, histórico Milho/Milho/Milho: ver "Seu plano atual" e 3 alternativas.

---

### P2: Idioma

**User Story**: As a usuário de qualquer país, I want the site in Portuguese, English or Spanish so that I understand it.

**Why P2**: O sistema é mundial; PT basta para a banca local.

**Acceptance Criteria**:

1. The system SHALL offer a language selector with "Português", "English", "Español", with Português selected when the site opens.
2. WHEN a user selects a language THEN the system SHALL show every fixed interface text in that language and pass the matching `idioma` ("pt", "en", "es") to the motor.

**Independent Test**: Trocar para English e ver abas, botões e explicações em inglês.

---

### P2: Painel "Por que confiar"

**User Story**: As a jurado ou técnico, I want to see where every number comes from and what the system does not do so that I trust the recommendation.

**Why P2**: Credibilidade; resposta às barreiras 2 e 3 do pitch.

**Acceptance Criteria**:

1. WHEN a point is selected THEN the system SHALL show a collapsible panel "Por que confiar" listing every entry of the motor's `fontes`.
2. The system SHALL show in that panel the limits text: dados regionais (~50 km); não diagnostica pragas ou doenças; janela de plantio estimada pelo clima; não considera irrigação.
3. The system SHALL link "NASA POWER" in that panel to `https://power.larc.nasa.gov/`.

---

### P3: Fotos do campo no mapa e alertas no Telegram

**User Story**: As a técnico, I want to see field photos sent through Telegram on the map and send a farm to the bot so that the site and the bot work as one system.

**Why P3**: Mostra a interligação na demo, mas depende do banco da feature 3.

**Acceptance Criteria**:

1. WHERE `core/db.py` is available the system SHALL draw one marker per observation returned by `listar_observacoes()`, distinct from the selected-point marker.
2. WHEN a user clicks an observation marker THEN the system SHALL show its date, text, `descricao_ia` and a thumbnail of the photo.
3. WHEN a user clicks "Atualizar fotos" THEN the system SHALL reload the observations from the database.
4. WHERE `core/db.py` is available, WHEN a user clicks "Receber alertas no Telegram" THEN the system SHALL create the farm for the selected point with `criar_fazenda` and open `https://t.me/<bot>?start=<id>`.
5. WHEN a user clicks "Receber alertas no Telegram" twice for the same point in the same session THEN the system SHALL reuse the farm id created the first time.

---

## Edge Cases

- IF the map click falls outside latitude [-90, 90] or longitude [-180, 180] (map wrap-around) THEN the system SHALL normalize longitude into [-180, 180] before calling the motor.
- WHEN the window is 390 px wide THEN the system SHALL show the cards stacked in one column with no horizontal page scroll.
- IF the motor raises `ValueError` THEN the system SHALL show its message next to the control that caused it.
- WHEN the motor is unavailable for a tab THEN the system SHALL keep the other tabs working.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| -------------- | ----- | ----- | ------ |
| SITE-01 | P1: Ponto — abertura | Design | Pending |
| SITE-02 | P1: Ponto — sem abas sem ponto | Design | Pending |
| SITE-03 | P1: Ponto — clique no mapa | Design | Pending |
| SITE-04 | P1: Ponto — botões da demo | Design | Pending |
| SITE-05 | P1: Ponto — país, coordenadas, selo | Design | Pending |
| SITE-06 | P1: Ponto — carregando | Design | Pending |
| SITE-07 | P1: Ponto — fora de terra | Design | Pending |
| SITE-08 | P1: Ponto — fonte indisponível | Design | Pending |
| SITE-09 | P1: Ponto — reuso na sessão | Design | Pending |
| SITE-10 | P1: Clima — resumo | Design | Pending |
| SITE-11 | P1: Clima — 5 cards | Design | Pending |
| SITE-12 | P1: Clima — modo anual | Design | Pending |
| SITE-13 | P1: Clima — gráfico | Design | Pending |
| SITE-14 | P1: Clima — anos sem estação | Design | Pending |
| SITE-15 | P1: Plantar — controles e padrões | Design | Pending |
| SITE-16 | P1: Plantar — recalcula ao mudar | Design | Pending |
| SITE-17 | P1: Plantar — cards na ordem | Design | Pending |
| SITE-18 | P1: Plantar — retorno ou sem dado | Design | Pending |
| SITE-19 | P1: Plantar — culturas ignoradas | Design | Pending |
| SITE-20 | P1: Plantar — prioridades zeradas | Design | Pending |
| SITE-21 | P1: Plantar — ranking vazio | Design | Pending |
| SITE-22 | P2: Planos — seletores | Design | Pending |
| SITE-23 | P2: Planos — histórico incompleto | Design | Pending |
| SITE-24 | P2: Planos — chama o motor | Design | Pending |
| SITE-25 | P2: Planos — atual primeiro | Design | Pending |
| SITE-26 | P2: Planos — campos de cada plano | Design | Pending |
| SITE-27 | P2: Idioma — seletor | Design | Pending |
| SITE-28 | P2: Idioma — troca tudo | Design | Pending |
| SITE-29 | P2: Confiar — fontes | Design | Pending |
| SITE-30 | P2: Confiar — limites | Design | Pending |
| SITE-31 | P2: Confiar — link POWER | Design | Pending |
| SITE-32 | P3: Fotos — marcadores | Design | Pending |
| SITE-33 | P3: Fotos — popup | Design | Pending |
| SITE-34 | P3: Fotos — atualizar | Design | Pending |
| SITE-35 | P3: Telegram — cria fazenda e abre bot | Design | Pending |
| SITE-36 | P3: Telegram — reuso do id | Design | Pending |
| SITE-37 | Edge: longitude normalizada | Design | Pending |
| SITE-38 | Edge: 390 px | Design | Pending |
| SITE-39 | Edge: ValueError no controle | Design | Pending |
| SITE-40 | Edge: abas independentes | Design | Pending |

**Coverage:** 40 total, 0 mapped to tasks, 40 unmapped ⚠️ (tasks come after approval)

---

## Implicit-requirement dimensions

| Dimension | Covered by |
| --------- | ---------- |
| Input validation & bounds | SITE-03, SITE-20, SITE-23, SITE-37, SITE-39 |
| Failure / partial-failure states | SITE-07, SITE-08, SITE-21, SITE-40 |
| Idempotency / retry / duplicate handling | SITE-09, SITE-36 |
| Auth boundaries & rate limits | Public site by user decision; repeated motor calls bounded by SITE-09 and the motor cache |
| Concurrency / ordering | N/A because each Streamlit session is isolated and the site keeps no shared state besides the database (feature 3) |
| Data lifecycle / expiry | N/A because the site stores nothing; farms and photos belong to feature 3 |
| Observability | N/A because errors surface to the user (SITE-07, SITE-08) and the motor already logs its requests (MOT-13) |
| External-dependency failure | SITE-08, SITE-40 |
| State-transition integrity | SITE-02, SITE-06 (no point → computing → result or error) |

---

## Sources

- `.specs/features/motor/spec.md` (aprovada) — contratos `contexto`, `clima_mudou`, `ranking_safra`, `planos_rotacao`.
- `.specs/STATE.md` AD-001, AD-003, AD-004.
- Notion: Guia do Kaue, Guia da Cecilia — estrutura de abas e controles (sem layout vinculante).

---

## Success Criteria

- [ ] Pitch: Rio Verde → 3 abas preenchidas em < 10 s; troca para Ludhiana mostra outro resultado.
- [ ] Nenhum número na tela sem uma fonte listada em "Por que confiar".
- [ ] Usável em celular de 390 px.
