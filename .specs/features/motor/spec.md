# Motor (núcleo `core/`) Specification

**Approved**: 2026-11-14 - user: "aprovo"

## Problem Statement

O agricultor precisa escolher uma rotação de culturas para os próximos anos sem saber o risco climático de cada opção, e os dados da NASA que mediriam esse risco não chegam até ele em forma de decisão. O motor transforma 30 anos de clima diário do NASA POWER e o solo do ponto em notas explicadas — risco de quebra, saúde do solo e retorno — para qualquer lugar do planeta. Site e bot são só portas de entrada para ele (AD-001, AD-004).

## Goals

- [ ] Para os 4 pontos da demo, `ranking_safra` devolve um ranking explicado em < 5 s com cache.
- [ ] Para os 4 pontos da demo, `clima_mudou` mostra diferenças entre 1995–2009 e 2010–2025.
- [ ] O motor funciona em qualquer ponto em terra firme, mesmo sem dado nacional (AD-003).

## Out of Scope

| Feature | Reason |
| ------- | ------ |
| Tela, bot, servidor MCP, LLM | Features 2 (site) e 3 (bot + MCP) |
| Banco SQLite (fazendas, fotos, alertas) | Pertence às features site e bot |
| Irrigação e arroz inundado | Balanço hídrico diferente; MVP trata só sequeiro |
| Pragas, doenças, compactação | O motor não diagnostica (AD-004) |
| Previsão do tempo e alertas em tempo real | Feature bot; o motor usa só histórico |
| Clima futuro (CMIP6), SMAP, MODIS | Features futuras (Deferred Ideas) |
| Culturas de ciclo longo (mandioca, cana) | Não cabem no modelo de safras de 3 anos |
| Manejo dentro do talhão | Resolução do POWER (~50 km) não permite |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Limite de quebra | Perda estimada > 20% | user: "Perda >20%; 1995–2009 × 2010–2025 (Recommended)" | y |
| Períodos comparados | 1995–2009 × 2010–2025 | mesma resposta | y |
| Pontos da demo | Rio Verde, Nakuru, Ludhiana, Ames | user: "Sim, esses 4 (Recommended)" | y |
| Idiomas dos textos do motor | pt, en, es; outro valor → en | user: "PT, EN e espanhol" | y |
| Umidade do solo na semeadura | Depleção inicial = 50% da TAW | Safra seguinte começa com solo parcialmente usado; meio-termo entre cheio e seco | n |
| Anos simulados | Semeaduras de 1995 a 2024 (ciclo precisa terminar até 2025-12-31) | Série do POWER vai até 2025 | n |
| Data de referência da estação | 1º/ago no hemisfério S, 1º/fev no N | Início da busca pela estação chuvosa; simplificação para regiões bimodais (ex.: Nakuru) | n |
| Classe climática do ponto | árido se chuva anual média < 500 mm; senão tropical se o mês mais frio tem tmédia ≥ 18 °C; subtropical se ≥ 0 °C; temperado se < 0 °C | Regra simples derivada só do POWER, para filtrar culturas sem dado nacional | n |
| Pesos padrão das prioridades | retorno 0,4 · segurança 0,4 · solo 0,2 | Usado quando o chamador não informa | n |
| Normalização das notas | segurança = 100 − risco_pct; solo = (nota_solo − 1) / 4 × 100; retorno = 100 × retorno / maior retorno entre as opções | Notas comparáveis de 0 a 100 | n |
| Parâmetros das culturas | Só culturas com todos os parâmetros do modelo preenchidos entram no cálculo | Hoje 5 de 20 culturas estão preenchidas e nenhuma validada | n |
| Candidatas por ponto | No máximo 5 culturas de 2ª safra/inverno/cobertura por ponto | Limita os planos de 3 anos a 125 combinações | n |
| Textura → `cad_mm` (lacuna achada na T8) | Saxton & Rawls (2006), θ33 − θ1500 em mm/m, matéria orgânica fixa em 2,5% | Spec não dizia a fórmula; ~143 mm/m para solo franco | n |
| Data 02-29 (lacuna achada na T4) | `data_mmdd` rejeita 02-29 | A semeadura se repete em 1995–2024 e a maioria dos anos não é bissexta | n |
| Chaves de `prioridades` (lacuna achada na T4) | `retorno`, `seguranca`, `solo`; ausente = 0; chave desconhecida → `ValueError` | Contrato não fixava os nomes | n |
| SoilGrids sem valor (mar/cidade) | Mesmo fallback `cad_mm = 100`, `fonte = "padrão"`; fallback não vai para o cache | Evita gravar um padrão como se fosse dado | n |
| Culturas não validadas (bloqueio da T18) | Milho e Sorgo granífero recebem os dias de estágio da FAO-56 Tab. 11 (linha citada em `fonte`), `validado=false`; só o Matheus marca `true`; todo resultado com cultura não validada sai com `preliminar = true` (MOT-63) | user: "Sim, os 3 passos (Recommended)" | y |
| Temporada incompleta (lacuna achada na T14) | Temporada que não termina até 2025-12-31 fica fora das médias (MOT-62) | user: "Descartar incompletas (Recommended)" | y |
| Solo nos 4 pontos da demo (T18) | Integração aceita `fonte = "padrão"` enquanto o SoilGrids responde 503; com cache de solo o teste continua valendo | user: "Aceitar 'padrão' por ora (Recommended)" | y |
| Início da estação (lacuna achada na T14) | A busca inclui a própria data de referência; o dia de início é o 1º dos 3 dias com ≥ 20 mm; "30 dias seguintes" contam após o dia de início | Spec não fixava os limites | n |
| Fim da estação (lacuna achada na T14) | Acumulado de 10 dias = os 10 dias que terminam no dia avaliado | Spec não fixava a janela | n |
| "Maior mudança" do resumo (lacuna achada na T14) | Variação relativa \|depois − antes\| / \|antes\| (antes = 0 vale 1); datas: deslocamento em dias / duração média da estação 1995–2009 | Torna grandezas diferentes comparáveis | n |
| Janela segura que cruza o ano (lacuna achada na T15) | Datas circulares (21/dez → 01/jan é uma sequência); empate fica com a que começa antes; tudo seguro → fim "12-21" | Spec não tratava a virada | n |
| Data de semeadura dos planos (lacuna achada na T17) | `data_semeadura` opcional; padrão 03-01 no hemisfério S e 09-01 no N | Spec não fixava | n |
| `nota_solo` vazia (lacuna achada na T17) | Vazia vale 3 (50 pontos, neutro) | 15 de 20 culturas sem nota | n |
| Risco e retorno do plano (lacuna achada na T17) | 28 janelas de 3 anos; `risco_pct` = 100 × quebras / 84; retorno = média das 3 culturas, None se faltar uma | Spec não fixava a agregação | n |

**Open questions:** none - all resolved or logged above (required before the spec is confirmed).

---

## User Stories

### P1: Dados de clima e solo de qualquer ponto ⭐ MVP

**User Story**: As a dev do site ou do bot, I want the motor to fetch climate, soil and country for any lat/lon so that every feature works anywhere on the planet.

**Why P1**: Todo o resto depende desses dados; o NASA POWER é o dado NASA obrigatório.

**Acceptance Criteria**:

1. WHEN `power.serie(lat, lon)` is called for a point without a cache file THEN the system SHALL request the NASA POWER daily point API with parameters `PRECTOTCORR,T2M_MAX,T2M_MIN,ALLSKY_SFC_SW_DWN,GWETROOT`, `community=AG`, from 1995-01-01 to 2025-12-31, and save the response to `cache/power_{lat:.2f}_{lon:.2f}.json`.
2. WHEN `power.serie(lat, lon)` is called for a point whose cache file exists and is valid JSON THEN the system SHALL return the data without any network request.
3. The system SHALL return from `power.serie` a DataFrame with one row per day and the columns `data, chuva, tmax, tmin, rad, umid_solo`.
4. The system SHALL replace the NASA POWER fill value -999 with NaN in the returned DataFrame.
5. IF the NASA POWER request fails or takes longer than 120 s and no cache file exists THEN the system SHALL raise `ErroFonteDados` with a message that names "NASA POWER".
6. IF a cache file exists but is not valid JSON THEN the system SHALL discard it and request the data again.
7. The system SHALL write cache files atomically (temporary file then rename) so that two simultaneous calls never leave a partial file.
8. IF latitude is outside [-90, 90] or longitude is outside [-180, 180] THEN the system SHALL raise `ValueError` before any network request.
9. WHEN `solo.agua_disponivel(lat, lon)` is called THEN the system SHALL return `cad_mm`, `argila_pct`, `areia_pct` and `fonte = "SoilGrids"` from the 0–30 cm layers of SoilGrids v2.0, cached in `cache/solo_{lat:.2f}_{lon:.2f}.json`.
10. IF the SoilGrids request fails and no cache file exists THEN the system SHALL return `cad_mm = 100`, `argila_pct = None`, `areia_pct = None` and `fonte = "padrão"`.
11. WHEN `pais.de(lat, lon)` is called THEN the system SHALL return `iso2`, `nome` and `hemisferio` (`"S"` when lat < 0, otherwise `"N"`) using `data/paises.geojson` with no network request.
12. IF the point lies inside no country polygon THEN the system SHALL return `iso2 = None` from `pais.de`.
13. WHEN the motor sends a request to NASA POWER or SoilGrids THEN the system SHALL log at INFO level the source name, the point and the duration in seconds.

**Independent Test**: Com os arquivos de cache dos 4 pontos, chamar `serie`, `agua_disponivel` e `de` sem internet e receber dados nos 4.

---

### P1: Seu clima mudou ⭐ MVP

**User Story**: As a agricultor (via site ou bot), I want to see how the climate of my area changed since 2010 so that I understand why my rotation may need to change.

**Why P1**: Abre o pitch e justifica a recomendação com dados da NASA.

**Acceptance Criteria**:

1. WHEN `clima.clima_mudou(lat, lon, idioma)` is called THEN the system SHALL return, for each period 1995–2009 and 2010–2025, the mean of: season rainfall (mm), season start date (MM-DD), season end date (MM-DD), number of dry spells per season and days with tmax ≥ 35 °C per season.
2. The system SHALL define the season start of a year as the first day after the reference date (1º/ago in hemisphere S, 1º/fev in hemisphere N) with ≥ 20 mm of rain in 3 consecutive days and no run of 10 consecutive days with < 1 mm in the following 30 days.
3. The system SHALL define the season end as the last day of the season whose 10-day accumulated rain is ≥ 10 mm.
4. The system SHALL count a dry spell as a run of ≥ 10 consecutive days with < 1 mm between season start and season end.
5. IF no season start is found in a year THEN the system SHALL exclude that year from the means and report the count in `anos_sem_estacao`.
6. IF fewer than 10 of the 31 years have a season start THEN the system SHALL return `modo = "anual"` and compare calendar-year rainfall and days with tmax ≥ 35 °C instead of season values.
7. The system SHALL return a one-sentence `resumo` in the requested `idioma` stating the largest change between the two periods.
8. The system SHALL return `chuva_por_ano` as a list of `{ano, chuva_mm}` with the calendar-year rainfall total for every year from 1995 to 2025.
9. IF a season does not end by 2025-12-31 THEN the system SHALL exclude it from the period means and count it in `anos_sem_estacao`.

**Independent Test**: Rodar para os 4 pontos e ver valores diferentes e um resumo em pt, en e es.

---

### P1: Ranking de culturas para uma safra ⭐ MVP

**User Story**: As a agricultor, I want to know which crop is safest and best to plant on a given date so that I can decide the next season with less risk.

**Why P1**: É a rede de segurança do MVP: sozinho já responde ao desafio.

**Acceptance Criteria**:

1. WHEN `modelo.ranking_safra(lat, lon, data_semeadura, prioridades, idioma)` is called THEN the system SHALL simulate each candidate crop of the point (from `contexto`) once per year from 1995 to 2024, sowing on `data_semeadura` (MM-DD).
2. The system SHALL compute daily reference evapotranspiration with Hargreaves: `ET0 = 0.0023 · Ra · (Tmean + 17.8) · √(Tmax − Tmin)`, with Ra in mm/day from latitude and day of year (FAO-56 eq. 21 × 0.408).
3. The system SHALL interpolate the crop coefficient Kc daily across the crop's four stages (initial, development, mid, late) from `kc_ini`, `kc_mid`, `kc_fim`.
4. The system SHALL run a daily soil-water balance with `TAW = cad_mm × raiz_m`, `RAW = p × TAW`, `Ks = 1` when depletion ≤ RAW and `Ks = (TAW − Dr) / (TAW − RAW)` otherwise, starting each season with depletion = 50% of TAW.
5. The system SHALL estimate the yield loss of a season as `Ky × (1 − ΣETa / ΣETc)` clipped to [0, 1].
6. The system SHALL count a season as a crop failure when its estimated loss is greater than 0.20.
7. The system SHALL return for each crop `risco_pct` = round(100 × failures / seasons simulated) and `anos_quebra` as the string `"<failures>/<seasons>"`.
8. The system SHALL return for each crop `nota` from 0 to 100 as the sum of `prioridades` weights times the normalized safety, soil and return scores, and SHALL sort the crops by `nota` descending.
9. IF return data is unavailable for every candidate crop THEN the system SHALL drop the return weight and rescale the other weights to sum 1.
10. The system SHALL return for each crop an `explicacao` in the requested `idioma` that states failures in 1995–2009 and in 2010–2025 (e.g. "faltou água em 9 de 15 anos desde 2010; antes eram 4 de 15").
11. IF `prioridades` has a negative weight or all weights are 0 THEN the system SHALL raise `ValueError`.
12. WHEN `prioridades` weights do not sum to 1 THEN the system SHALL rescale them to sum 1.
13. IF `data_semeadura` is not a valid MM-DD date THEN the system SHALL raise `ValueError`.
14. IF a candidate crop lacks any model parameter (stage days, Kc, raiz, p, Ky) THEN the system SHALL exclude it from the ranking and list it in `culturas_ignoradas`.
15. The system SHALL return from `ranking_safra` a dict with `itens` (the ranked crops), `culturas_ignoradas` and `fontes`.
16. WHILE the point's POWER and SoilGrids data are cached the system SHALL return `ranking_safra` in less than 5 s.

**Independent Test**: Rodar para Rio Verde com semeadura em 03-15 e ver o milho com risco maior que o sorgo, com explicação.

---

### P1: Contexto do ponto ⭐ MVP

**User Story**: As a dev do site ou do bot, I want to know the country, candidate crops and data sources for a point so that the user sees what the recommendation is based on.

**Why P1**: Sem candidatas não há ranking; sem fontes não há "Por que confiar".

**Acceptance Criteria**:

1. WHEN `contexto.contexto(lat, lon)` is called THEN the system SHALL return `pais`, `culturas`, `fontes` and `nivel_precisao`.
2. WHEN the point's country has rows in `data/faostat.csv` THEN the system SHALL return as candidates the crops of those rows that also exist in `culturas.csv` and set `nivel_precisao = "pais"`.
3. WHEN the point's country has no rows in `data/faostat.csv` THEN the system SHALL return as candidates the crops of `culturas.csv` whose `climas` include the point's climate class and set `nivel_precisao = "clima"`.
4. The system SHALL classify the point's climate as árido when mean annual rain < 500 mm, otherwise tropical when the coldest month mean temperature ≥ 18 °C, subtropical when ≥ 0 °C, and temperado when < 0 °C.
5. The system SHALL always include "NASA POWER" in `fontes`, and "SoilGrids" or "padrão" according to the soil source used.
6. IF `pais.de` returns `iso2 = None` THEN the system SHALL raise `ErroPontoInvalido` with the message "ponto fora de terra".

**Independent Test**: Rodar para os 4 pontos e um ponto no oceano.

---

### P2: Planos de rotação de 3 anos

**User Story**: As a agricultor, I want to compare 3-year rotation plans with what I do today so that I choose a rotation that protects the soil and survives the new climate.

**Why P2**: É o diferencial do desafio (rotação, saúde do solo), mas depende do ranking pronto.

**Acceptance Criteria**:

1. WHEN `modelo.planos_rotacao(lat, lon, historico, prioridades, idioma)` is called THEN the system SHALL evaluate every 3-year sequence of the point's candidate second-season, winter and cover crops, using at most 5 candidates.
2. The system SHALL simulate each plan over every 3-year window of consecutive years from 1995 to 2024 and set its `risco_pct` as the share of simulated seasons with failure.
3. The system SHALL set a plan's `nota_solo` (1–5) as the mean of: diversity (1 family = 1, 2 families = 3, 3+ = 5), legume presence (any crop with `fixa_n` = 5, none = 1) and the mean `nota_solo` of its crops.
4. The system SHALL include the current plan built from the last 3 items of `historico`, flagged `atual = true`, even when it is not among the best.
5. The system SHALL return the 3 best plans by `nota` plus the current plan.
6. The system SHALL return for each non-current plan an `explicacao` in the requested `idioma` that states its difference from the current plan in risk points and in return.
7. IF `historico` contains a crop not present in `culturas.csv` THEN the system SHALL raise `ValueError` naming the unknown crops.
8. WHILE the point's data are cached the system SHALL return `planos_rotacao` in less than 10 s.

**Independent Test**: Rio Verde com histórico Milho, Milho, Milho mostra o plano atual e 3 alternativas com menos risco.

---

### P2: Janela de plantio

**User Story**: As a agricultor, I want to know until which date it is still safe to sow a crop so that I don't plant too late.

**Why P2**: Responde "até quando planto?" no bot; usa o mesmo motor.

**Acceptance Criteria**:

1. WHEN `clima.janela_plantio(lat, lon, cultura)` is called THEN the system SHALL compute `risco_pct` for sowing on days 01, 11 and 21 of every month.
2. WHERE the crop has `t_min_c` defined the system SHALL set `risco_pct = 100` and `motivo = "frio"` for sowing dates whose mean tmin over the following 30 days is below `t_min_c`.
3. The system SHALL return `fim_seguro` as the last date of the longest continuous run of sowing dates with `risco_pct` < 20.
4. IF no sowing date has `risco_pct` < 20 THEN the system SHALL return `fim_seguro = None`.

**Independent Test**: Milho em Rio Verde devolve uma data-limite; milho em Ames não tem janela no inverno (motivo frio).

---

### P2: Retorno por país

**User Story**: As a agricultor, I want to see the expected return of each option so that I weigh risk against income.

**Why P2**: Fora do Brasil, o retorno vem do FAOSTAT; o ranking funciona sem ele.

**Acceptance Criteria**:

1. WHEN `data/faostat.csv` has a row for the point's country and the crop THEN the system SHALL set `retorno = produtividade_t_ha × (1 − mean loss) × preco_usd_t` and `moeda = "USD"`.
2. IF there is no row for the point's country and the crop THEN the system SHALL set `retorno = None`.

---

### P3: Adaptador Brasil

**User Story**: As a agricultor no Brasil, I want municipal data to be used so that the recommendation is more precise.

**Why P3**: Melhora a precisão, mas o sistema já funciona sem ele (AD-003).

**Acceptance Criteria**:

1. WHERE `core/adaptadores/brasil.py` provides data for the point the system SHALL use its crops and municipal yield, set `nivel_precisao = "municipal"` and `moeda = "BRL"`.

---

## Edge Cases

- IF `idioma` is not "pt", "en" or "es" THEN the system SHALL produce texts in English.
- IF a POWER day has NaN rain THEN the system SHALL treat it as 0 mm; IF it has NaN temperature THEN the system SHALL interpolate linearly from neighbouring days.
- WHEN a crop cycle crosses 31 December THEN the system SHALL continue the simulation into the next calendar year.
- IF a crop used in a result has `validado` different from true THEN the system SHALL set `preliminar = true` on that ranking item, rotation plan or planting-window result; otherwise `preliminar = false`.

---

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| -------------- | ----- | ----- | ------ |
| MOT-01 | P1: Dados — POWER request + cache | Design | Pending |
| MOT-02 | P1: Dados — cache hit sem rede | Design | Pending |
| MOT-03 | P1: Dados — colunas do DataFrame | Design | Pending |
| MOT-04 | P1: Dados — -999 → NaN | Design | Pending |
| MOT-05 | P1: Dados — falha POWER | Design | Pending |
| MOT-06 | P1: Dados — cache inválido | Design | Pending |
| MOT-07 | P1: Dados — escrita atômica | Design | Pending |
| MOT-08 | P1: Dados — lat/lon inválidos | Design | Pending |
| MOT-09 | P1: Dados — SoilGrids | Design | Pending |
| MOT-10 | P1: Dados — fallback solo | Design | Pending |
| MOT-11 | P1: Dados — país e hemisfério | Design | Pending |
| MOT-12 | P1: Dados — ponto fora de país | Design | Pending |
| MOT-13 | P1: Dados — log de requisições | Design | Pending |
| MOT-14 | P1: Clima — médias por período | Design | Pending |
| MOT-15 | P1: Clima — início da estação | Design | Pending |
| MOT-16 | P1: Clima — fim da estação | Design | Pending |
| MOT-17 | P1: Clima — veranicos | Design | Pending |
| MOT-18 | P1: Clima — anos sem estação | Design | Pending |
| MOT-19 | P1: Clima — modo anual | Design | Pending |
| MOT-20 | P1: Clima — resumo no idioma | Design | Pending |
| MOT-21 | P1: Ranking — simulação 1995–2024 | Design | Pending |
| MOT-22 | P1: Ranking — ET0 Hargreaves | Design | Pending |
| MOT-23 | P1: Ranking — Kc por fase | Design | Pending |
| MOT-24 | P1: Ranking — balanço hídrico | Design | Pending |
| MOT-25 | P1: Ranking — perda FAO-33 | Design | Pending |
| MOT-26 | P1: Ranking — quebra > 20% | Design | Pending |
| MOT-27 | P1: Ranking — risco e anos_quebra | Design | Pending |
| MOT-28 | P1: Ranking — nota e ordenação | Design | Pending |
| MOT-29 | P1: Ranking — sem retorno | Design | Pending |
| MOT-30 | P1: Ranking — explicação | Design | Pending |
| MOT-31 | P1: Ranking — pesos inválidos | Design | Pending |
| MOT-32 | P1: Ranking — pesos reescalados | Design | Pending |
| MOT-33 | P1: Ranking — data inválida | Design | Pending |
| MOT-34 | P1: Ranking — cultura sem parâmetros | Design | Pending |
| MOT-35 | P1: Ranking — formato de saída | Design | Pending |
| MOT-36 | P1: Ranking — < 5 s com cache | Design | Pending |
| MOT-37 | P1: Contexto — campos | Design | Pending |
| MOT-38 | P1: Contexto — nível país | Design | Pending |
| MOT-39 | P1: Contexto — nível clima | Design | Pending |
| MOT-40 | P1: Contexto — classe climática | Design | Pending |
| MOT-41 | P1: Contexto — fontes | Design | Pending |
| MOT-42 | P1: Contexto — fora de terra | Design | Pending |
| MOT-43 | P2: Planos — combinações | Design | Pending |
| MOT-44 | P2: Planos — janelas de 3 anos | Design | Pending |
| MOT-45 | P2: Planos — nota de solo | Design | Pending |
| MOT-46 | P2: Planos — plano atual | Design | Pending |
| MOT-47 | P2: Planos — top 3 + atual | Design | Pending |
| MOT-48 | P2: Planos — explicação vs atual | Design | Pending |
| MOT-49 | P2: Planos — histórico inválido | Design | Pending |
| MOT-50 | P2: Planos — < 10 s | Design | Pending |
| MOT-51 | P2: Janela — decêndios | Design | Pending |
| MOT-52 | P2: Janela — frio | Design | Pending |
| MOT-53 | P2: Janela — fim seguro | Design | Pending |
| MOT-54 | P2: Janela — sem janela | Design | Pending |
| MOT-55 | P2: Retorno — FAOSTAT | Design | Pending |
| MOT-56 | P2: Retorno — sem dado | Design | Pending |
| MOT-57 | P3: Adaptador Brasil | Design | Pending |
| MOT-58 | Edge: idioma desconhecido | Design | Pending |
| MOT-59 | Edge: NaN no POWER | Design | Pending |
| MOT-60 | Edge: ciclo cruza o ano | Design | Pending |
| MOT-61 | P1: Clima — chuva por ano (pedido pelo site, SITE-13) | Design | Pending |
| MOT-62 | P1: Clima — temporada incompleta fora das médias | Design | Pending |
| MOT-63 | Edge: resultado com cultura não validada marcado `preliminar` | Design | Pending |

**Coverage:** 63 total, 0 mapped to tasks, 60 unmapped ⚠️ (tasks come after approval)

---

## Implicit-requirement dimensions

| Dimension | Covered by |
| --------- | ---------- |
| Input validation & bounds | MOT-08, MOT-31, MOT-33, MOT-49, MOT-58 |
| Failure / partial-failure states | MOT-05, MOT-06, MOT-10 |
| Idempotency / retry / duplicate handling | MOT-02, MOT-07 (cache determinístico, escrita atômica) |
| Auth boundaries & rate limits | N/A because the motor is a local library with no users; POWER calls are bounded by the cache (MOT-02) |
| Concurrency / ordering | MOT-07 |
| Data lifecycle / expiry | N/A because the historical range 1995–2025 is fixed, so cached files never go stale |
| Observability | MOT-13 |
| External-dependency failure | MOT-05, MOT-10 |
| State-transition integrity | N/A because every motor function is stateless |

---

## Sources

- Conversa de planejamento e Notion (página "Arquitetura do MVP", "Guias da Equipe") - arquitetura, contratos e tarefas.
- `.specs/STATE.md` AD-001..AD-004 - decisões do time.
- FAO-56 (eq. 21, eq. 52, cap. 8) e FAO-33 - fórmulas do modelo.

---

## Success Criteria

- [ ] Os 4 pontos da demo produzem ranking, "clima mudou" e planos sem internet (cache versionado).
- [ ] Rio Verde, semeadura 03-15: milho com `risco_pct` maior que sorgo.
- [ ] Nenhum número sai do motor sem `fontes` acompanhando.
