# Motor Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/motor/design.md`
**Status**: Approved
**Approved**: 2026-11-14 - user: "Aprovo"
**Build**: `.venv/bin/python -m compileall -q core app.py mcp_server.py bot.py; .venv/bin/ruff check .`
**Run unit**: `.venv/bin/python -m pytest -v tests/unit`
**Run integ**: `.venv/bin/python -m pytest -v tests/integracao`

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: none - strong defaults applied. Test types chosen by the user: "pytest: unit + integração com cache (Recommended)".

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Domínio (balanco, clima, modelo, contexto, global_ctx, validacao, textos, culturas) | unit | Todos os ramos; 1:1 com os ACs; todo edge case listado tem teste | `tests/unit/test_<modulo>.py` | `.venv/bin/python -m pytest -v tests/unit` |
| Acesso a dados (power, solo, pais, cache, adaptadores) | unit (rede simulada com monkeypatch, fixtures em disco) | Caminho feliz + cache + falha + validação | `tests/unit/test_<modulo>.py` | `.venv/bin/python -m pytest -v tests/unit` |
| Integração nos 4 pontos da demo | integration (cache versionado, sem rede) | Tempo de resposta e resultados reais dos 4 pontos | `tests/integracao/test_demo.py` | `.venv/bin/python -m pytest -v tests/integracao` |
| Exceções / dependências | none | - (build gate only) | - | build gate only |

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Tarefas com testes de unidade | `.venv/bin/python -m pytest -v tests/unit` |
| Full | Tarefa de integração | `.venv/bin/python -m pytest -v tests/unit tests/integracao` |
| Build | Fim de fase e tarefas sem teste | `.venv/bin/python -m compileall -q core app.py mcp_server.py bot.py; .venv/bin/ruff check .; .venv/bin/python -m pytest -v tests/unit` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

### Phase 1: Fundação

```
T1 → T2
T1 → T3
T1 → T4
T1 → T5
T1 → T6
```

### Phase 2: Dados externos

```
T2 → T7
T3 → T7
T4 → T7
T7 → T8
T4 → T9
```

### Phase 3: Cálculo e contexto

```
T6 → T10
T1 → T11
T1 → T12
T7 → T13
T8 → T13
T9 → T13
T11 → T13
T12 → T13
```

### Phase 4: Clima

```
T5 → T14
T7 → T14
T9 → T14
T14 → T15
T10 → T15
T8 → T15
T14 → T19
T16 → T20
T17 → T20
T15 → T20
```

### Phase 5: Ranking e planos

```
T4 → T16
T5 → T16
T10 → T16
T11 → T16
T13 → T16
T16 → T17
```

### Phase 6: Integração

```
T15 → T18
T16 → T18
T17 → T18
T19 → T18
T20 → T18
```

---

## Task Breakdown

### T1: Adicionar ruff às dependências

**What**: Incluir `ruff` no `requirements.txt` para o gate de build.
**Where**: `requirements.txt`
**Depends on**: None
**Reuses**: `requirements.txt` existente
**Requirement**: (infraestrutura do build)

**Done when**:

- [x] `ruff` listado e instalado no ambiente
- [x] `ruff check .` roda sem erro na estrutura atual

**Tests**: none
**Gate**: build
**Status**: ✅ Complete

---

### T2: Exceções do domínio

**What**: `ErroFonteDados` e `ErroPontoInvalido`.
**Where**: `core/erros.py`
**Depends on**: T1
**Reuses**: -
**Requirement**: MOT-05, MOT-42

**Done when**:

- [x] As duas classes existem e herdam de `Exception`
- [x] Gate build passa

**Tests**: none
**Gate**: build
**Status**: ✅ Complete

---

### T3: Cache JSON atômico

**What**: `caminho`, `ler` (None se ausente ou inválido) e `gravar` (tmp + `os.replace`).
**Where**: `core/cache.py`
**Depends on**: T1
**Reuses**: stdlib
**Requirement**: MOT-07

**Done when**:

- [x] Nome do arquivo `cache/{prefixo}_{lat:.2f}_{lon:.2f}.json`
- [x] `ler` devolve None para JSON inválido
- [x] Gravação nunca deixa arquivo parcial (teste simula falha no meio)
- [x] Gate quick passa; 3 testes

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T4: Validação de entradas

**What**: `ponto(lat, lon)`, `data_mmdd(s)`, `pesos(prioridades)` (padrão 0,4/0,4/0,2; reescala para somar 1).
**Where**: `core/validacao.py`
**Depends on**: T1
**Reuses**: stdlib
**Requirement**: MOT-31, MOT-32, MOT-33

**Done when**:

- [x] `ValueError` para lat/lon fora do intervalo, data MM-DD inválida, peso negativo ou todos zero
- [x] Pesos reescalados para somar 1
- [x] Gate quick passa; 4 testes

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T5: Textos em pt/en/es

**What**: `t(chave, idioma, **valores)` com os modelos de frase usados por `clima` e `modelo`; idioma desconhecido → en.
**Where**: `core/textos.py`
**Depends on**: T1
**Reuses**: -
**Requirement**: MOT-58

**Done when**:

- [x] Mesma chave existe nos 3 idiomas
- [x] Idioma "fr" devolve o texto em inglês
- [x] Gate quick passa; 2 testes

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T6: Leitura das culturas

**What**: `carregar(path)` → dict por nome; `completa(c)` verifica `CAMPOS_MODELO`.
**Where**: `core/culturas.py`
**Depends on**: T1
**Reuses**: `data/culturas.csv`
**Requirement**: MOT-34

**Done when**:

- [x] Lê o CSV real (20 culturas) e um CSV de fixture
- [x] `completa` é False quando falta qualquer campo do modelo
- [x] Gate quick passa; 3 testes

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T7: NASA POWER com cache

**What**: `serie(lat, lon)` conforme spec: parâmetros, período, cache, -999→NaN, timeout 120 s, erro, log INFO.
**Where**: `core/power.py`
**Depends on**: T2, T3, T4
**Reuses**: `core/cache.py`, `core/validacao.py`, `core/erros.py`
**Requirement**: MOT-01, MOT-02, MOT-03, MOT-04, MOT-05, MOT-06, MOT-08

**Done when**:

- [x] Rede simulada com monkeypatch (nenhum teste acessa a internet)
- [x] Gate quick passa; 7 testes

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T8: SoilGrids com cache e fallback

**What**: `agua_disponivel(lat, lon)`: argila/areia 0–30 cm → `cad_mm`; fallback 100 mm "padrão"; log INFO.
**Where**: `core/solo.py`
**Depends on**: T7
**Reuses**: `core/cache.py`, padrão de `core/power.py`
**Requirement**: MOT-09, MOT-10, MOT-13

**Done when**:

- [x] Teste de log cobre POWER e SoilGrids
- [x] Gate quick passa; 3 testes

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T9: País e hemisfério offline

**What**: `de(lat, lon, path)` com shapely sobre `data/paises.geojson`.
**Where**: `core/pais.py`
**Depends on**: T4
**Reuses**: `core/validacao.py`
**Requirement**: MOT-11, MOT-12

**Done when**:

- [x] Testes com mini GeoJSON de fixture (2 polígonos)
- [x] Gate quick passa; 2 testes

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T10: Balanço hídrico FAO-56

**What**: `ra_mm`, `et0_hargreaves`, `kc_diario`, `simular_safra` (Ks, depleção inicial 50% TAW, perda FAO-33, quebra > 0,20, NaN, ciclo que cruza o ano).
**Where**: `core/balanco.py`
**Depends on**: T6
**Reuses**: `core/culturas.py`
**Requirement**: MOT-22, MOT-23, MOT-24, MOT-25, MOT-26, MOT-59, MOT-60

**Done when**:

- [x] Valores conferidos à mão em séries sintéticas (ex.: chuva diária = ETc → perda 0; sem chuva → perda limitada a Ky)
- [x] Gate quick passa; 7 testes

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T11: Produtividade e preço por país

**What**: `linhas_pais(iso2)` e `retorno(iso2, cultura, perda_media)` lendo `data/faostat.csv`.
**Where**: `core/global_ctx.py`
**Depends on**: T1
**Reuses**: -
**Requirement**: MOT-55, MOT-56

**Done when**:

- [x] Testes com CSV de fixture
- [x] Gate quick passa; 2 testes

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T12: Gancho do adaptador Brasil

**What**: `dados(lat, lon)` → None sem `data/brasil_municipal.csv`; com o arquivo, culturas e produtividade do município mais próximo.
**Where**: `core/adaptadores/brasil.py`
**Depends on**: T1
**Reuses**: -
**Requirement**: MOT-57

**Done when**:

- [x] Sem arquivo devolve None; com fixture devolve dados
- [x] Gate quick passa; 2 testes

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T13: Contexto do ponto

**What**: `contexto(lat, lon)` e `classe_climatica(serie)`: adaptador → FAOSTAT → clima; fontes; fora de terra.
**Where**: `core/contexto.py`
**Depends on**: T7, T8, T9, T11, T12
**Reuses**: `pais`, `power`, `solo`, `global_ctx`, `adaptadores.brasil`, `culturas`
**Requirement**: MOT-37, MOT-38, MOT-39, MOT-40, MOT-41, MOT-42, MOT-57

**Done when**:

- [x] Fontes externas substituídas por fakes nos testes
- [x] Gate quick passa; 7 testes

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T14: Seu clima mudou

**What**: `estacao(...)` e `clima_mudou(lat, lon, idioma)` conforme os critérios de início, fim, veranicos, calor, anos sem estação e modo anual.
**Where**: `core/clima.py`
**Depends on**: T5, T7, T9
**Reuses**: `power`, `pais`, `textos`
**Requirement**: MOT-14, MOT-15, MOT-16, MOT-17, MOT-18, MOT-19, MOT-20, MOT-61

**Done when**:

- [x] Séries sintéticas com estação conhecida (início, fim e veranicos plantados)
- [x] `chuva_por_ano` com 31 anos (1995–2025)
- [x] Gate quick passa; 8 testes

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T15: Janela de plantio

**What**: `janela_plantio(lat, lon, cultura)` nos dias 01/11/21, motivo "frio", `fim_seguro`.
**Where**: `core/clima.py` (modify)
**Depends on**: T14, T10, T8
**Reuses**: `balanco.simular_safra`
**Requirement**: MOT-51, MOT-52, MOT-53, MOT-54

**Done when**:

- [x] Gate quick passa; 4 testes novos (11 em `test_clima.py`)

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T16: Ranking de uma safra

**What**: `ranking_safra(lat, lon, data_semeadura, prioridades, idioma)` → `{itens, culturas_ignoradas, fontes}`.
**Where**: `core/modelo.py`
**Depends on**: T4, T5, T10, T11, T13
**Reuses**: `contexto`, `balanco`, `global_ctx`, `validacao`, `textos`
**Requirement**: MOT-21, MOT-27, MOT-28, MOT-29, MOT-30, MOT-34, MOT-35

**Done when**:

- [x] Fakes para contexto/série/solo nos testes
- [x] Gate quick passa; 7 testes

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T17: Planos de rotação de 3 anos

**What**: `planos_rotacao(lat, lon, historico, prioridades, idioma)`: até 5 candidatas, janelas de 3 anos, nota de solo, plano atual, top 3, explicação.
**Where**: `core/modelo.py` (modify)
**Depends on**: T16
**Reuses**: perdas por (cultura, ano) calculadas uma vez
**Requirement**: MOT-43, MOT-44, MOT-45, MOT-46, MOT-47, MOT-48, MOT-49

**Done when**:

- [x] Gate quick passa; 7 testes novos (14 em `test_modelo.py`)

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T19: Temporada incompleta fora das médias

**What**: Em `clima_mudou`, a temporada que não termina até 2025-12-31 sai das médias e entra em `anos_sem_estacao` (decisão de 2026-11-15, user: "Descartar incompletas (Recommended)").
**Where**: `core/clima.py`
**Depends on**: T14
**Reuses**: `estacao`
**Requirement**: MOT-62

**Done when**:

- [x] Série sintética cuja última estação passa de 31/dez/2025 não entra na média 2010–2025
- [x] Gate quick passa; 1 teste novo

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T20: Culturas FAO e marca `preliminar`

**What**: Preencher em `data/culturas.csv` os dias de estágio de Milho e Sorgo granífero com a FAO-56 Tab. 11 (linha citada em `fonte`, `validado=false`) e marcar `preliminar` no ranking, nos planos e na janela de plantio (user: "Sim, os 3 passos (Recommended)").
**Where**: `data/culturas.csv`, `core/culturas.py`, `core/modelo.py`, `core/clima.py`
**Depends on**: T15, T16, T17
**Reuses**: `culturas.completa`
**Requirement**: MOT-63

**Done when**:

- [x] Milho e Sorgo granífero completos, `validado=false`, fonte com a linha da tabela
- [x] Gate quick passa; 2 testes novos

**Tests**: unit
**Gate**: quick
**Status**: ✅ Complete

---

### T18: Integração nos 4 pontos da demo

**What**: Testes com o cache versionado dos 4 pontos: tempo do ranking e dos planos, e o critério de sucesso de Rio Verde.
**Where**: `tests/integracao/test_demo.py`
**Depends on**: T15, T16, T17, T19, T20
**Reuses**: `cache/` versionado, `data/paises.geojson`, `data/culturas.csv` validado
**Requirement**: MOT-36, MOT-50

**Pré-requisitos externos (bloqueiam esta tarefa)**: cache dos 4 pontos e `data/paises.geojson` baixados fora da rede corporativa (Nascimento); `dias_*` e parâmetros de pelo menos milho e sorgo validados no `culturas.csv` (Matheus).

**Done when**:

- [ ] Rodam sem internet
- [ ] Rio Verde, semeadura 03-15: milho com `risco_pct` maior que sorgo
- [ ] Gate full passa; 3 testes

**Tests**: integration
**Gate**: full
**Status**: ❌ Blocked — nenhuma das 20 culturas de `data/culturas.csv` tem `dias_*` (0 completas: ranking e planos saem vazios nos 4 pontos); faltam também `cache/solo_*.json` dos 4 pontos e `data/faostat.csv`

---

## Checks

**C1** - Sem cache, `serie` chama o POWER com os 5 parâmetros, `community=AG`, 19950101–20251231, e grava `cache/power_{lat:.2f}_{lon:.2f}.json` (MOT-01, AC 1)
Proof: run unit | test_power.py::test_sem_cache_chama_api_e_salva PASSED

**C2** - Com cache válido, `serie` não faz nenhuma requisição (MOT-02, AC 2)
Proof: run unit | test_power.py::test_com_cache_nao_usa_rede PASSED

**C3** - O DataFrame tem uma linha por dia e as colunas `data, chuva, tmax, tmin, rad, umid_solo` (MOT-03, AC 3)
Proof: run unit | test_power.py::test_colunas_um_dia_por_linha PASSED

**C4** - O valor -999 do POWER vira NaN (MOT-04, AC 4)
Proof: run unit | test_power.py::test_menos_999_vira_nan PASSED

**C5** - Falha ou timeout sem cache levanta `ErroFonteDados` com "NASA POWER" na mensagem (MOT-05, AC 5)
Proof: run unit | test_power.py::test_falha_sem_cache_erro_fonte PASSED

**C6** - Cache com JSON inválido é descartado e os dados são buscados de novo (MOT-06, AC 6)
Proof: run unit | test_power.py::test_cache_invalido_busca_de_novo PASSED

**C7** - Uma gravação interrompida nunca deixa arquivo de cache parcial (MOT-07, AC 7)
Proof: run unit | test_cache.py::test_gravacao_atomica PASSED

**C8** - lat fora de [-90, 90] ou lon fora de [-180, 180] levanta `ValueError` sem requisição (MOT-08, AC 8)
Proof: run unit | test_power.py::test_ponto_invalido_sem_rede PASSED

**C9** - `agua_disponivel` devolve `cad_mm`, `argila_pct`, `areia_pct`, `fonte="SoilGrids"` das camadas 0–30 cm e grava `cache/solo_...json` (MOT-09, AC 9)
Proof: run unit | test_solo.py::test_soilgrids_0_30cm_e_cache PASSED

**C10** - Falha do SoilGrids sem cache devolve `cad_mm=100`, argila/areia None, `fonte="padrão"` (MOT-10, AC 10)
Proof: run unit | test_solo.py::test_falha_usa_padrao PASSED

**C11** - `pais.de` devolve iso2, nome e hemisfério "S" para lat < 0 e "N" caso contrário, sem rede (MOT-11, AC 11)
Proof: run unit | test_pais.py::test_pais_e_hemisferio PASSED

**C12** - Ponto fora de qualquer país devolve `iso2 = None` (MOT-12, AC 12)
Proof: run unit | test_pais.py::test_fora_de_pais_iso2_none PASSED

**C13** - Cada requisição ao POWER e ao SoilGrids gera log INFO com fonte, ponto e duração (MOT-13, AC 13)
Proof: run unit | test_solo.py::test_log_requisicoes_power_e_solo PASSED

**C14** - `clima_mudou` devolve, para 1995–2009 e 2010–2025, as médias de chuva da estação, início, fim, veranicos e dias ≥ 35 °C (MOT-14, Clima AC 1)
Proof: run unit | test_clima.py::test_medias_por_periodo PASSED

**C15** - O início da estação é o 1º dia após 1º/ago (S) ou 1º/fev (N) com ≥ 20 mm em 3 dias e sem 10 dias secos nos 30 seguintes (MOT-15, Clima AC 2)
Proof: run unit | test_clima.py::test_inicio_da_estacao PASSED

**C16** - O fim da estação é o último dia com chuva acumulada de 10 dias ≥ 10 mm (MOT-16, Clima AC 3)
Proof: run unit | test_clima.py::test_fim_da_estacao PASSED

**C17** - Um veranico é uma sequência ≥ 10 dias com < 1 mm entre início e fim (MOT-17, Clima AC 4)
Proof: run unit | test_clima.py::test_conta_veranicos PASSED

**C18** - Ano sem início de estação fica fora das médias e é contado em `anos_sem_estacao` (MOT-18, Clima AC 5)
Proof: run unit | test_clima.py::test_anos_sem_estacao PASSED

**C19** - Com menos de 10 dos 31 anos com estação, `modo = "anual"` e a comparação usa o ano civil (MOT-19, Clima AC 6)
Proof: run unit | test_clima.py::test_modo_anual PASSED

**C20** - `resumo` é uma frase no idioma pedido (pt, en, es) com a maior mudança entre os períodos (MOT-20, Clima AC 7)
Proof: run unit | test_clima.py::test_resumo_no_idioma PASSED

**C21** - `ranking_safra` simula cada candidata uma vez por ano de 1995 a 2024 na data pedida (MOT-21, Ranking AC 1)
Proof: run unit | test_modelo.py::test_simula_1995_a_2024 PASSED

**C22** - ET0 segue Hargreaves `0.0023 · Ra · (Tmean + 17.8) · √(Tmax − Tmin)` com Ra da FAO-56 eq. 21 × 0,408 (MOT-22, Ranking AC 2)
Proof: run unit | test_balanco.py::test_et0_hargreaves PASSED

**C23** - Kc diário interpola `kc_ini`, `kc_mid`, `kc_fim` pelas 4 fases (MOT-23, Ranking AC 3)
Proof: run unit | test_balanco.py::test_kc_por_fase PASSED

**C24** - O balanço usa TAW = cad × raiz, RAW = p × TAW, Ks da FAO-56 e começa com depleção de 50% da TAW (MOT-24, Ranking AC 4)
Proof: run unit | test_balanco.py::test_balanco_ks_e_deplecao_inicial PASSED

**C25** - A perda é `Ky × (1 − ΣETa/ΣETc)` limitada a [0, 1] (MOT-25, Ranking AC 5)
Proof: run unit | test_balanco.py::test_perda_fao33_limitada PASSED

**C26** - Uma safra é quebra quando a perda é maior que 0,20 (e não quando é exatamente 0,20) (MOT-26, Ranking AC 6)
Proof: run unit | test_balanco.py::test_quebra_acima_de_20 PASSED

**C27** - `risco_pct` = round(100 × quebras / safras) e `anos_quebra` = "quebras/safras" (MOT-27, Ranking AC 7)
Proof: run unit | test_modelo.py::test_risco_e_anos_quebra PASSED

**C28** - `nota` de 0 a 100 é a soma ponderada das notas normalizadas e os itens vêm em ordem decrescente de nota (MOT-28, Ranking AC 8)
Proof: run unit | test_modelo.py::test_nota_e_ordenacao PASSED

**C29** - Sem retorno para nenhuma cultura, o peso do retorno sai e os outros são reescalados para somar 1 (MOT-29, Ranking AC 9)
Proof: run unit | test_modelo.py::test_sem_retorno_reescala_pesos PASSED

**C30** - `explicacao` no idioma pedido cita quebras em 1995–2009 e em 2010–2025 (MOT-30, Ranking AC 10)
Proof: run unit | test_modelo.py::test_explicacao_antes_e_depois PASSED

**C31** - Peso negativo ou todos os pesos zero levantam `ValueError` (MOT-31, Ranking AC 11)
Proof: run unit | test_validacao.py::test_pesos_invalidos PASSED

**C32** - Pesos que não somam 1 são reescalados para somar 1 (MOT-32, Ranking AC 12)
Proof: run unit | test_validacao.py::test_pesos_reescalados PASSED

**C33** - `data_semeadura` que não é MM-DD válida levanta `ValueError` (MOT-33, Ranking AC 13)
Proof: run unit | test_validacao.py::test_data_mmdd_invalida PASSED

**C34** - Candidata sem algum parâmetro do modelo fica fora do ranking e aparece em `culturas_ignoradas` (MOT-34, Ranking AC 14)
Proof: run unit | test_modelo.py::test_cultura_sem_parametros_ignorada PASSED

**C35** - `ranking_safra` devolve dict com `itens`, `culturas_ignoradas` e `fontes` (MOT-35, Ranking AC 15)
Proof: run unit | test_modelo.py::test_formato_saida_ranking PASSED

**C36** - Com cache, `ranking_safra` responde em menos de 5 s nos 4 pontos (MOT-36, Ranking AC 16)
Proof: run integ | test_demo.py::test_ranking_menos_de_5s PASSED

**C37** - `contexto` devolve `pais`, `culturas`, `fontes` e `nivel_precisao` (MOT-37, Contexto AC 1)
Proof: run unit | test_contexto.py::test_campos PASSED

**C38** - País com linhas no FAOSTAT: candidatas = culturas dessas linhas que existem no CSV, `nivel_precisao = "pais"` (MOT-38, Contexto AC 2)
Proof: run unit | test_contexto.py::test_nivel_pais PASSED

**C39** - País sem FAOSTAT: candidatas = culturas cujos `climas` incluem a classe do ponto, `nivel_precisao = "clima"` (MOT-39, Contexto AC 3)
Proof: run unit | test_contexto.py::test_nivel_clima PASSED

**C40** - Classe climática: árido < 500 mm/ano; senão tropical (mês mais frio ≥ 18 °C), subtropical (≥ 0 °C), temperado (< 0 °C) (MOT-40, Contexto AC 4)
Proof: run unit | test_contexto.py::test_classe_climatica PASSED

**C41** - `fontes` sempre tem "NASA POWER" e "SoilGrids" ou "padrão" conforme o solo usado (MOT-41, Contexto AC 5)
Proof: run unit | test_contexto.py::test_fontes PASSED

**C42** - Ponto sem país levanta `ErroPontoInvalido("ponto fora de terra")` (MOT-42, Contexto AC 6)
Proof: run unit | test_contexto.py::test_fora_de_terra PASSED

**C43** - `planos_rotacao` avalia todas as sequências de 3 anos com no máximo 5 candidatas (≤ 125 planos) (MOT-43, Planos AC 1)
Proof: run unit | test_modelo.py::test_planos_combinacoes_max_5 PASSED

**C44** - Cada plano é simulado em todas as janelas de 3 anos consecutivos de 1995 a 2024 e `risco_pct` é a fração de safras com quebra (MOT-44, Planos AC 2)
Proof: run unit | test_modelo.py::test_planos_janelas_3_anos PASSED

**C45** - `nota_solo` do plano é a média de diversidade (1/3/5), leguminosa (5 ou 1) e média das `nota_solo` das culturas (MOT-45, Planos AC 3)
Proof: run unit | test_modelo.py::test_planos_nota_solo PASSED

**C46** - O plano atual (3 últimos do histórico) aparece com `atual = true` mesmo fora dos melhores (MOT-46, Planos AC 4)
Proof: run unit | test_modelo.py::test_planos_inclui_atual PASSED

**C47** - A resposta tem os 3 melhores planos por nota mais o plano atual (MOT-47, Planos AC 5)
Proof: run unit | test_modelo.py::test_planos_top3_mais_atual PASSED

**C48** - Cada plano não atual tem `explicacao` no idioma pedido com a diferença em pontos de risco e em retorno frente ao atual (MOT-48, Planos AC 6)
Proof: run unit | test_modelo.py::test_planos_explicacao_vs_atual PASSED

**C49** - Histórico com cultura fora do CSV levanta `ValueError` citando as desconhecidas (MOT-49, Planos AC 7)
Proof: run unit | test_modelo.py::test_planos_historico_invalido PASSED

**C50** - Com cache, `planos_rotacao` responde em menos de 10 s nos 4 pontos (MOT-50, Planos AC 8)
Proof: run integ | test_demo.py::test_planos_menos_de_10s PASSED

**C51** - `janela_plantio` calcula `risco_pct` para os dias 01, 11 e 21 de cada mês (36 datas) (MOT-51, Janela AC 1)
Proof: run unit | test_clima.py::test_janela_decendios PASSED

**C52** - Com `t_min_c` definido, datas cuja tmin média nos 30 dias seguintes fica abaixo dele têm `risco_pct = 100` e `motivo = "frio"` (MOT-52, Janela AC 2)
Proof: run unit | test_clima.py::test_janela_frio PASSED

**C53** - `fim_seguro` é a última data da maior sequência contínua com `risco_pct` < 20 (MOT-53, Janela AC 3)
Proof: run unit | test_clima.py::test_janela_fim_seguro PASSED

**C54** - Sem nenhuma data com risco < 20, `fim_seguro = None` (MOT-54, Janela AC 4)
Proof: run unit | test_clima.py::test_janela_sem_data_segura PASSED

**C55** - Com linha no FAOSTAT, `retorno = produtividade × (1 − perda média) × preço` e `moeda = "USD"` (MOT-55, Retorno AC 1)
Proof: run unit | test_global_ctx.py::test_retorno_faostat PASSED

**C56** - Sem linha para país e cultura, `retorno = None` (MOT-56, Retorno AC 2)
Proof: run unit | test_global_ctx.py::test_sem_linha_retorno_none PASSED

**C57** - Com dados do adaptador Brasil, o contexto usa suas culturas e produtividade, `nivel_precisao = "municipal"` e `moeda = "BRL"` (MOT-57, Adaptador AC 1)
Proof: run unit | test_contexto.py::test_adaptador_brasil_municipal PASSED

**C58** - Idioma diferente de pt, en e es produz textos em inglês (MOT-58, Edge 1)
Proof: run unit | test_textos.py::test_idioma_desconhecido_usa_en PASSED

**C59** - Chuva NaN conta como 0 mm e temperatura NaN é interpolada dos dias vizinhos (MOT-59, Edge 2)
Proof: run unit | test_balanco.py::test_nan_chuva_zero_temp_interpolada PASSED

**C60** - Um ciclo que cruza 31/dez continua no ano seguinte (MOT-60, Edge 3)
Proof: run unit | test_balanco.py::test_ciclo_cruza_o_ano PASSED

**C61** - `clima_mudou` devolve `chuva_por_ano` com o total de chuva do ano civil para cada ano de 1995 a 2025 (31 itens) (MOT-61, Clima AC 8)
Proof: run unit | test_clima.py::test_chuva_por_ano PASSED

**C62** - Uma temporada que não termina até 2025-12-31 fica fora das médias e conta em `anos_sem_estacao` (MOT-62, Clima AC 9)
Proof: run unit | test_clima.py::test_temporada_incompleta_fora_das_medias PASSED

**C63** - Resultado com cultura `validado` ≠ true sai com `preliminar = true`; com todas validadas, `false` (MOT-63, Edge 4)
Proof: run unit | test_modelo.py::test_marca_preliminar_quando_nao_validada PASSED

---

## Handoff

The feature's live state, written as it happens - a compaction gives no warning.

**Settled mid-build:** Execução por sub-agentes, 1 por lote — user: "Sub-agentes, 1 por lote (Recommended)". Exclusões pendentes viram um commit separado antes da T1 — user: "Commit só das exclusões (Recommended)". Comandos de build/teste usam `.venv/` (Python 3.14, sem pip global). Execução pausada após T9: especificar todas as features primeiro, depois o time implementa — user: "lembrando que vamos especificar primeiro e depois cada um do time vai especificar". MOT-61 (`chuva_por_ano`) acrescentado à spec, à T14 e ao check C61 — user: "faz isso mesmo Recomendo acrescentar à spec do motor um critério novo, MOT-61".
**Dispatched:** batch worker 1 (Phases 1–2, T1–T9) at HEAD 47f6c1b — returned (T1–T9 done, 24 unit tests green, HEAD eac16a1) · execução retomada 2026-11-15 — user: "Vamos começar a implementar nossa parte a parte de EDVAN" · batch worker 2 (Phases 3–4, T10–T15) at HEAD dc9334a — returned (T10–T15 done, 54 unit tests green, HEAD = commit da T15) · batch worker 3 (Phases 5–6, T16–T18) at HEAD 05f6769 — returned (T16–T17 done, 68 unit tests green, HEAD 1ddf041; T18 blocked: culturas.csv sem `dias_*`, sem cache de solo e sem faostat.csv)
**Walked:** none

---

## Phase Execution Map

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6

Phase 1:  T1, T2, T3, T4, T5, T6   (fundação)
Phase 2:  T7, T8, T9               (POWER, SoilGrids, país)
Phase 3:  T10, T11, T12, T13       (balanço, FAOSTAT, adaptador, contexto)
Phase 4:  T14, T15, T19            (clima mudou, janela, temporada incompleta)
Phase 5:  T16, T17                 (ranking, planos)
Phase 6:  T20, T18                 (culturas FAO e preliminar, integração nos 4 pontos)
```

Execution is strictly sequential - there is no intra-phase parallelism.
