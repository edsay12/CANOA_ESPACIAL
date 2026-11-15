# Onde fica sua terra? verification

**Verdict**: PASS
**Proofs**: `proofs.md` at b13b9a4
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `captures/onde-fica-sua-terra-desktop.running.png` e revisão independente em `screens.md` | yes — composição a 1366 × 978, mapa sem marcador e botão desabilitado conforme AD-006. |
| C2 | `captures/onde-fica-sua-terra-mobile.running.png` e revisão independente em `screens.md` | yes — composição a 390 × 1035, sem marcador na abertura nem rolagem horizontal, com botão desabilitado. |
| C3 | Percurso em Chrome com dois cliques, mais `test_mapa.py::test_clique_normaliza_longitude_e_arredonda` | yes — os cliques renderizaram `-10.89, -50.73` e `-0.86, 33.82`, respectivamente, com um único marcador após cada seleção. |
| C4 | `test_site_location.py::test_each_demo_selects_its_coordinates` | yes — o teste fixa os quatro exemplos e verifica rótulo, coordenadas e marcador. |
| C5 | `test_localizacao.py::test_context_shows_country_coordinates_and_precision` | yes — o texto completo é verificado para os selos municipal, país e clima. |
| C6 | Percurso em navegador com resposta controlada de dois segundos | yes — o indicador aparece antes do contexto. |
| C7 | Percurso em desktop e celular, mais `test_site_location.py::test_climate_buttons_are_disabled_before_and_after_selection` | yes — o percurso cobre os rótulos exibidos e o teste verifica o estado desabilitado de cada controle nos dois estados de seleção. |
| C8 | `test_site_location.py::test_language_switch_translates_screen_and_keeps_point` | yes — o teste verifica os textos fixos, as duas ações de clima e o selo em cada idioma, preservando o marcador. |
| C9 | `test_site_location.py::test_wrapped_map_click_queries_normalized_longitude` e `test_pontos.py::test_longitude_normalizada` | yes — a integração compara as coordenadas enviadas ao motor e o teste unitário cobre a normalização nos dois sentidos. |
| C10 | `test_site_location.py::test_off_land_map_click_allows_demo_selection` | yes — o teste integrado recebe a rejeição pelo mapa e recupera o contexto pelo botão de exemplo. |
| C11 | `test_localizacao.py::test_source_failure_displays_error_and_allows_retry` | yes — compara a mensagem e aciona a tentativa, que exibe o contexto do mesmo ponto. |
| C12 | `test_site_location.py::test_reselecting_point_reuses_context_in_same_session` | yes — o teste seleciona coordenadas brutas distintas que normalizam para o ponto já consultado. |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C4 aceita exemplos alterados no teste de integração | `tests/app/test_site_location.py:31` usa `DEMO.items()` como expectativa. A checagem de valores em `tests/web/test_pontos.py` testa somente o dicionário. | Fixar no AppTest os quatro pares de rótulo e coordenadas e conferir a lista de botões, o marcador e a consulta. | `bfed1ce` |
| C5 aceita que todo contexto exiba selo municipal | `tests/web/test_localizacao.py:29` injeta apenas contexto municipal. | Exercitar os três valores de precisão retornados pelo motor e comparar o texto completo de cada contexto. | `bfed1ce` |
| C8 aceita textos fixos em português após trocar o idioma | `tests/app/test_site_location.py:47`–`49` só verificam o título, a ação desktop e o marcador. | Conferir também os textos fixos da trilha e do cabeçalho, as instruções e dicas responsivas, o rótulo dos exemplos e a ação mobile em cada idioma. | `bfed1ce` |
| C10 aceita que a tela perca a capacidade de escolher outro ponto depois do erro | `tests/web/test_localizacao.py:42` altera `session_state.ponto` diretamente no painel isolado. | Disparar a rejeição no app e escolher outro local usando um controle da tela, verificando o contexto recuperado. | `bfed1ce` |
| C12 aceita cache limitado ao mesmo caminho de seleção | `tests/app/test_site_location.py:63`–`65` repetem o botão de Rio Verde, com Nakuru entre as seleções. | Reabrir o mesmo ponto normalizado a partir de coordenadas brutas diferentes e conferir a contagem de chamadas ao motor. | `bfed1ce` |

## Independent Examples

- `(43.061, -218.648)` marcou `(43.06, 141.35)` e exibiu o selo de país com resposta controlada. Depois de outras seleções, `(43.064, 141.354)` recuperou o mesmo contexto e o motor foi consultado uma única vez para esse ponto.
- `(11.254, -173.751)` exibiu o aviso de terra firme com uma rejeição controlada. A seleção seguinte em `(-33.923, 18.422)` marcou `(-33.92, 18.42)` e exibiu “Estimado pelo clima”.
- A arte vinculante simplifica o litoral e omite ilhas. Na escala nativa do SVG desktop, `(18.49, -69.90)` é identificado como República Dominicana pelo motor e cai no fundo de água a 23 px da silhueta mais próxima.

Nos dois primeiros exemplos, o caminho executado usou `clicar`, `marcador`, `Servico` e `exibir_contexto` com respostas do motor controladas.
