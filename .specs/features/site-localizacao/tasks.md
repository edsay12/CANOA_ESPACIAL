# Site — Onde fica sua terra? Tasks

**Design**: [Design da primeira tela](design.md)  
**Status**: In Progress  
**Approved**: 2026-11-15 - user: "Aprovo, pode começar a implementação"  
**Branch**: `codex/feat/site-location`  
**Build**: `.venv/Scripts/python.exe -m compileall -q core web app.py mcp_server.py bot.py; .venv/Scripts/python.exe -m ruff check .`  
**Run location**: `.venv/Scripts/python.exe -m pytest -v tests/web tests/app`

## Test Coverage Matrix

Fonte: plano de testes da [feature Site](../site/tasks.md) e testes existentes em `tests/web` e `tests/integracao`. A base atual tem 19 testes em `tests/web`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Textos, mapa e integração com o serviço | Unit e integração | Idiomas, ativos válidos, coordenadas, contexto e falhas | `tests/web/test_*.py` | `.venv/Scripts/python.exe -m pytest -v tests/web` |
| Tela Streamlit | Integração com AppTest | Seleção dos exemplos, troca de idioma, estado do botão, contexto e reuso em sessão | `tests/app/test_site_location.py` | `.venv/Scripts/python.exe -m pytest -v tests/web tests/app` |
| Mapa interativo e layout | Navegador | Clique e marcador, carregamento e dois tamanhos do Figma | Capturas em `captures/` | Executar `.venv/Scripts/python.exe -m streamlit run app.py` e fazer o percurso descrito nos checks. |

## Gate Check Commands

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Textos, ativos, mapa e contexto | `.venv/Scripts/python.exe -m pytest -v tests/web` |
| Full | Abertura integrada | `.venv/Scripts/python.exe -m pytest -v tests/web tests/app` |
| Build | Encerramento da implementação | Executar os comandos de **Build** e **Run location** do cabeçalho. |

## Execution Plan

### Phase 1: Location screen

```
T1 → T5
T2 → T3 → T5
T4 → T5
```

## Task Breakdown

### T1: Adicionar os textos da tela de localização

**What**: Acrescentar ao catálogo os textos da abertura em português, inglês e espanhol e os rótulos de clima do desktop e do celular.  
**Where**: `web/i18n.py`  
**Depends on**: None  
**Reuses**: Catálogo `TEXTOS` e função `t()`.  
**Requirement**: LOC-07, LOC-08

**Done when**:

- [x] Os textos em português correspondem aos frames e as mesmas chaves estão disponíveis nos três idiomas.
- [x] Gate quick passa com pelo menos 20 testes.

**Tests**: Unit em `tests/web/test_i18n.py`, incluindo um teste novo do conjunto de textos.  
**Gate**: Quick  
**Commit**: `feat(site): add location screen translations`

### T2: Incorporar os ativos locais do Figma

**What**: Salvar os SVGs usados na abertura desktop e mobile nos arquivos locais que o mapa e a tela carregarão.  
**Where**: `assets/site-location/`  
**Depends on**: None  
**Requirement**: LOC-01, LOC-02

**Done when**:

- [x] Os SVGs locais estão completos, têm as dimensões originais e estão associados aos respectivos usos no desktop e no celular.
- [x] Gate quick passa com pelo menos 21 testes.

**Tests**: Unit em `tests/web/test_site_location_assets.py`, incluindo um teste novo dos arquivos e dimensões.  
**Gate**: Quick  
**Commit**: `feat(site): add Figma location assets`

### T3: Implementar o mapa interativo

**What**: Montar o mapa-múndi da abertura com a arte local, devolver o ponto normalizado de um clique e desenhar o marcador nas coordenadas selecionadas.  
**Where**: `web/mapa.py`  
**Depends on**: T2  
**Reuses**: `web.pontos.normalizar`, Folium e streamlit-folium.  
**Requirement**: LOC-01, LOC-02, LOC-03, LOC-09

**Done when**:

- [x] O mapa vazio renderiza a arte, um novo ponto substitui o marcador e o clique com longitude fora do intervalo é normalizado.
- [x] Gate quick passa com pelo menos 23 testes.

**Tests**: Unit em `tests/web/test_mapa.py`, com pelo menos dois testes novos para coordenadas e marcador.  
**Gate**: Quick  
**Commit**: `feat(site): build the interactive location map`

### T4: Apresentar o contexto do local

**What**: Exibir a consulta do local, o contexto retornado e os estados de erro.  
**Where**: `web/localizacao.py`  
**Depends on**: None  
**Reuses**: `web.servico.Servico.contexto` e as mensagens e selos já disponíveis em `web.i18n`.  
**Requirement**: LOC-05, LOC-06, LOC-10, LOC-11, LOC-12

**Done when**:

- [x] O painel apresenta país, coordenadas e selo quando recebe contexto e oferece as respostas aprovadas para fora de terra firme e indisponibilidade.
- [x] Gate quick passa com pelo menos 26 testes.

**Tests**: Integração isolada em `tests/web/test_localizacao.py`, com pelo menos três testes novos para sucesso e falhas do motor.  
**Gate**: Quick  
**Commit**: `feat(site): show the selected location context`

### T5: Montar a abertura responsiva em Streamlit

**What**: Integrar trilha, cabeçalho, seletor de idioma, mapa, quatro exemplos, contexto e botão de clima em uma tela responsiva.  
**Where**: `app.py`  
**Depends on**: T1, T3, T4  
**Reuses**: `web.pontos.DEMO`, `web.servico.Servico`, `web.mapa`, `web.localizacao` e `web.i18n`.  
**Requirement**: LOC-01, LOC-02, LOC-03, LOC-04, LOC-05, LOC-06, LOC-07, LOC-08, LOC-09, LOC-10, LOC-11, LOC-12

**Done when**:

- [x] A abertura corresponde a `.specs/features/site-localizacao/captures/onde-fica-sua-terra-desktop.png` e `.specs/features/site-localizacao/captures/onde-fica-sua-terra-mobile.png`, com o desvio do botão registrado em AD-006.
- [x] O ponto escolhido é compartilhado entre o mapa e o painel, permanece na troca de idioma e o botão de clima continua desabilitado.
- [x] Gate full passa com pelo menos 30 testes.

**Tests**: Integração em `tests/app/test_site_location.py`, com pelo menos quatro testes novos, e verificação em navegador.  
**Gate**: Full  
**Commit**: `feat(site): assemble the responsive location screen`

## Checks

**C1** - Abrir a 1366 px mostra a composição desktop com mapa sem ponto selecionado e o botão de clima desabilitado (LOC-01, AC 1).  
Proof: browser captures/onde-fica-sua-terra-desktop.running.png

**C2** - Abrir a 390 px mostra a composição mobile, sem ponto selecionado e sem rolagem horizontal, com o botão de clima desabilitado (LOC-02, AC 2).  
Proof: browser captures/onde-fica-sua-terra-mobile.running.png

**C3** - Um clique no mapa cria um marcador nas coordenadas arredondadas a duas casas e um segundo clique substitui o primeiro (LOC-03, AC 3).  
Proof: walk - clicar duas vezes em pontos distintos no mapa e conferir coordenadas e marcador único

**C4** - Os quatro exemplos produzem os respectivos marcadores nas coordenadas de demonstração (LOC-04, AC 4).  
Proof: run location | test_site_location.py::test_each_demo_selects_its_coordinates PASSED

**C5** - Com contexto disponível, a tela exibe país, coordenadas e selo de precisão do ponto escolhido (LOC-05, AC 5).  
Proof: run location | test_localizacao.py::test_context_shows_country_coordinates_and_precision PASSED

**C6** - Enquanto o contexto está em processamento, a tela mostra um indicador de carregamento (LOC-06, AC 6).  
Proof: walk - selecionar um ponto com uma resposta do motor retardada e observar o indicador antes do contexto

**C7** - O botão de clima permanece desabilitado antes e depois da seleção; cada largura mostra seu rótulo (LOC-07, AC 7).  
Proof: walk - em desktop e celular conferir rótulo, estado semântico desabilitado e ausência de ação antes e depois de selecionar

**C8** - Alternar entre português, inglês e espanhol traduz os textos fixos e mantém o ponto selecionado (LOC-08, AC 8).  
Proof: run location | test_site_location.py::test_language_switch_translates_screen_and_keeps_point PASSED

**C9** - Clicar em uma longitude fora de [-180, 180] envia a longitude normalizada ao motor (LOC-09, Edge 1).  
Proof: run location | test_site_location.py::test_wrapped_map_click_queries_normalized_longitude PASSED

**C10** - A rejeição de um ponto fora de terra firme mostra a mensagem aprovada e o usuário pode escolher outro lugar (LOC-10, Edge 2).  
Proof: run location | test_localizacao.py::test_off_land_point_displays_error_and_allows_new_location PASSED

**C11** - A indisponibilidade da fonte mostra a mensagem aprovada e uma nova tentativa pode obter o contexto (LOC-11, Edge 3).  
Proof: run location | test_localizacao.py::test_source_failure_displays_error_and_allows_retry PASSED

**C12** - Repetir a solicitação de contexto disponível do mesmo ponto normalizado na sessão não faz outra consulta ao motor (LOC-12, Edge 4).  
Proof: run location | test_site_location.py::test_reselecting_point_reuses_context_in_same_session PASSED

## Handoff

**Settled mid-build:** none  
**Dispatched:** none  
**Walked:** Abertura em Chrome a 1366 × 978 e 390 × 1035. Dois cliques no mapa mobile substituíram o marcador. Rio Verde exibiu suas coordenadas no desktop. English traduziu a tela com o marcador preservado. O botão de clima ficou desabilitado em ambos os tamanhos, antes e depois da seleção. Uma resposta controlada de dois segundos mostrou o indicador antes de exibir o contexto.

## Phase Execution Map

```
Phase 1: T1 → T5
         T2 → T3 → T5
         T4 → T5
```

Ordem dos commits em inglês: T1, T2, T3, T4, T5.
