# Motor verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at afdfc97 (HEAD 3c64725 changes only tasks.md)
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `test_power.py` `test_sem_cache_chama_api_e_salva` | yes - URL, 5 parâmetros, AG, datas, timeout 120 e conteúdo do cache |
| C2 | `test_power.py` `test_com_cache_nao_usa_rede` | yes |
| C3 | `test_power.py` `test_colunas_um_dia_por_linha` | yes - ordem das colunas, datas e mapeamento de valores |
| C4 | `test_power.py` `test_menos_999_vira_nan` | yes - int e float, vizinhos intactos |
| C5 | `test_power.py` `test_falha_sem_cache_erro_fonte` | yes - timeout, conexão e HTTP 503; timeout de 120 s fixado em C1 |
| C6 | `test_power.py` `test_cache_invalido_busca_de_novo` | yes |
| C7 | `test_cache.py` `test_gravacao_atomica` | yes - falha no meio do dump preserva o arquivo e não deixa .tmp |
| C8 | `test_power.py` `test_ponto_invalido_sem_rede` | yes - os 4 lados; limites exatos em `test_validacao.py::test_ponto_fora_do_intervalo` |
| C9 | `test_solo.py` `test_soilgrids_0_30cm_e_cache` | partial - média 0–30 cm e cache exatos, mas `cad_mm` só em 100–200, mais frouxo que a fórmula registrada (Saxton & Rawls dá 137,6) |
| C10 | `test_solo.py` `test_falha_usa_padrao` | yes - 4 modos de falha, timeout 10 s, padrão fora do cache |
| C11 | `test_pais.py` `test_pais_e_hemisferio` | yes - lat 0 → "N"; arquivo real conferido à mão nos 4 pontos |
| C12 | `test_pais.py` `test_fora_de_pais_iso2_none` | yes |
| C13 | `test_solo.py` `test_log_requisicoes_power_e_solo` | yes - nível INFO, fonte, ponto e segundos |
| C14 | `test_clima.py` `test_medias_por_periodo` | yes - 5 médias exatas nos dois períodos, calor fora da estação excluído |
| C15 | `test_clima.py` `test_inicio_da_estacao` | yes - antes da referência, falso início, 9 × 10 dias secos, 19,98 × 20,01 mm, hemisfério N |
| C16 | `test_clima.py` `test_fim_da_estacao` | yes - 5 mm não estende, 10 mm estende |
| C17 | `test_clima.py` `test_conta_veranicos` | yes - 10 conta, 9 não |
| C18 | `test_clima.py` `test_anos_sem_estacao` | yes |
| C19 | `test_clima.py` `test_modo_anual` | yes - 9 anos → anual, 10 → estação |
| C20 | `test_clima.py` `test_resumo_no_idioma` | yes - frase exata em pt, en, es e fallback |
| C21 | `test_modelo.py` `test_simula_1995_a_2024` | yes |
| C22 | `test_balanco.py` `test_et0_hargreaves` | yes - Ra contra o exemplo 8 da FAO-56 |
| C23 | `test_balanco.py` `test_kc_por_fase` | yes - limites de cada fase e pontos intermediários |
| C24 | `test_balanco.py` `test_balanco_ks_e_deplecao_inicial` | yes - Ks = 1, Ks < 1 e depleção inicial de 50% |
| C25 | `test_balanco.py` `test_perda_fao33_limitada` | yes - 0, Ky, corte em 1 e caso intermediário |
| C26 | `test_balanco.py` `test_quebra_acima_de_20` | yes - 0,20 exato não é quebra |
| C27 | `test_modelo.py` `test_risco_e_anos_quebra` | yes - inclui perda exatamente 0,20 |
| C28 | `test_modelo.py` `test_nota_e_ordenacao` | yes - notas exatas e ordem |
| C29 | `test_modelo.py` `test_sem_retorno_reescala_pesos` | yes |
| C30 | `test_modelo.py` `test_explicacao_antes_e_depois` | yes |
| C31 | `test_validacao.py` `test_pesos_invalidos` | yes for the named cases - NaN passa (finding) |
| C32 | `test_validacao.py` `test_pesos_reescalados` | yes |
| C33 | `test_validacao.py` `test_data_mmdd_invalida` | yes |
| C34 | `test_modelo.py` `test_cultura_sem_parametros_ignorada` | yes - e não é simulada |
| C35 | `test_modelo.py` `test_formato_saida_ranking` | yes |
| C36 | `test_demo.py` `test_ranking_menos_de_5s` | yes - não exige `itens` não vazio, mas os 4 pontos rodam com 1–2 culturas (conferido) |
| C37 | `test_contexto.py` `test_campos` | yes |
| C38 | `test_contexto.py` `test_nivel_pais` | yes - cultura do FAOSTAT fora do CSV é filtrada |
| C39 | `test_contexto.py` `test_nivel_clima` | yes |
| C40 | `test_contexto.py` `test_classe_climatica` | yes - 18,0 × 17,9 e 0 × −0,1 |
| C41 | `test_contexto.py` `test_fontes` | yes |
| C42 | `test_contexto.py` `test_fora_de_terra` | yes - mensagem exata |
| C43 | `test_modelo.py` `test_planos_combinacoes_max_5` | yes |
| C44 | `test_modelo.py` `test_planos_janelas_3_anos` | yes - 1995 só na 1ª posição, 2024 só na 3ª |
| C45 | `test_modelo.py` `test_planos_nota_solo` | yes - segue `fixa_n` booleano do CSV, não o "= 5" do texto (finding) |
| C46 | `test_modelo.py` `test_planos_inclui_atual` | yes |
| C47 | `test_modelo.py` `test_planos_top3_mais_atual` | yes |
| C48 | `test_modelo.py` `test_planos_explicacao_vs_atual` | yes |
| C49 | `test_modelo.py` `test_planos_historico_invalido` | yes |
| C50 | `test_demo.py` `test_planos_menos_de_10s` | yes |
| C51 | `test_clima.py` `test_janela_decendios` | yes |
| C52 | `test_clima.py` `test_janela_frio` | yes - 9,8 × 13,2 °C em torno de 10 |
| C53 | `test_clima.py` `test_janela_fim_seguro` | yes - 20% exato, sequência que cruza o ano |
| C54 | `test_clima.py` `test_janela_sem_data_segura` | yes |
| C55 | `test_global_ctx.py` `test_retorno_faostat` | no - testa `global_ctx.retorno`, que nenhum código chama; o ranking usa `modelo._retorno` (a fórmula está coberta por `test_nota_e_ordenacao`) |
| C56 | `test_global_ctx.py` `test_sem_linha_retorno_none` | no - mesma função sem uso; `retorno = None` do ranking está coberto por `test_nota_e_ordenacao` (cultura C) |
| C57 | `test_contexto.py` `test_adaptador_brasil_municipal` | yes |
| C58 | `test_textos.py` `test_idioma_desconhecido_usa_en` | yes - também em C20 e C30 |
| C59 | `test_balanco.py` `test_nan_chuva_zero_temp_interpolada` | yes |
| C60 | `test_balanco.py` `test_ciclo_cruza_o_ano` | yes |
| C61 | `test_clima.py` `test_chuva_por_ano` | yes - 31 itens, NaN como 0 |
| C62 | `test_clima.py` `test_temporada_incompleta_fora_das_medias` | no - só cobre chuva até o último dia; temporada de 2025 com o fim de dezembro seco entra nas médias (finding) |
| C63 | `test_modelo.py` `test_marca_preliminar_quando_nao_validada` | yes - janela em `test_clima.py::test_janela_marca_preliminar` |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| MOT-62: temporada de 2025 cortada pelo fim da série entra nas médias quando os últimos 10 dias de dezembro são secos | `core/clima.py:105` só exclui quando `fim` é o último dia da série. Exemplo próprio: 1995–2024 com estação 15/out–31/mar, 2025 com chuva de 15/out a 18/dez → `anos_sem_estacao = 0` e 2010–2025 tem fim médio 03-25 e chuva menor. O teste de C62 (`tests/unit/test_clima.py:236`) só usa chuva até 31/dez | Tratar como incompleta toda estação cuja janela (referência + 1 ano) passa do fim da série, salvo quando o fim já está confirmado dentro da série (ex.: 10-dias < 10 mm por um prazo fixo antes de 31/dez); o prazo é decisão do usuário. Acrescentar o caso "dezembro seco" ao teste de C62 | 2040275 — C62 (`test_temporada_incompleta_fora_das_medias` cobre 31/dez, 18/dez e 02/dez; decisão do usuário: 30 dias) |
| `planos_rotacao` levanta `ValueError` para cultura conhecida sem parâmetros no histórico; nenhum critério pede isso e nenhum check o cobre | `core/modelo.py:106-108`. `planos_rotacao(Rio Verde, ["Soja","Milho","Soja"])` → `ValueError: culturas do histórico sem parâmetros do modelo: ['Soja']` - a rotação mais comum de Rio Verde quebra no site e no bot | Perguntar ao usuário o comportamento (ex.: plano atual sem risco, com a cultura em `culturas_ignoradas`, ou erro explícito); acrescentar critério novo com ID e check | ff8f490 — C65 (`test_planos_historico_com_cultura_sem_parametros`; MOT-65 decidido pelo usuário) |
| C55/C56 provam uma função que o motor não usa | `core/global_ctx.py:22` `retorno` não é chamada; `core/modelo.py:28` `_retorno` refaz a conta com `ctx["produtividade"]`. Trocar `(1 − perda)` em `modelo._retorno` não quebra C55 | Fazer `modelo` usar uma só função (ou apagar `global_ctx.retorno`) e apontar C55/C56 para testes do ranking que fixam `retorno = produtividade × (1 − perda média) × preço`, `moeda = "USD"` e `None` sem linha | ff8f490 — C55/C56 (`test_modelo.py::test_retorno_faostat`, `test_sem_linha_retorno_none`; `global_ctx.retorno` removido) |
| C9 aceita qualquer `cad_mm` entre 100 e 200 | `tests/unit/test_solo.py:49`; a fórmula registrada nas Assumptions (Saxton & Rawls 2006, MO 2,5%) dá 137,6 mm/m para 21,3% argila e 41,7% areia | `assert r["cad_mm"] == pytest.approx(137.6, abs=0.1)` | ffec12f — C9 (`approx(137.6, abs=0.1)`) |
| Peso NaN passa pela validação e todas as notas saem NaN | `core/validacao.py:35-41`: `pesos({"retorno": nan, "seguranca": 1})` → `{nan, nan, nan}` | Recusar pesos não finitos (`math.isfinite`) com `ValueError` e incluir o caso em `test_pesos_invalidos` | ffec12f — C31 (NaN e infinito em `test_pesos_invalidos`) |
| MOT-45 diz "`fixa_n` = 5", mas a coluna é booleana e código e teste usam `true` | `data/culturas.csv` coluna `fixa_n` = true/false; `core/modelo.py:86` | Registrar nas Assumptions da spec (linha nova, sem editar o critério) que leguminosa = `fixa_n` true | 410ba82 — linha de Assumptions "Leguminosa no plano" na spec |

Observações sem finding: `ranking_safra` e `planos_rotacao` chamam `solo.agua_disponivel` duas vezes (contexto e modelo) e o padrão não vai para o cache, então com o SoilGrids travado cada chamada espera 2 × 10 s - fora da condição "com cache" de MOT-36/MOT-50, mas visível no site. O adaptador Brasil usa o município mais próximo sem limite de distância; hoje não há `data/brasil_municipal.csv`. Os testes de C36/C50 não exigem `itens` não vazio.
