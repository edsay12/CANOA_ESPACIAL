# motor proofs

**HEAD**: 3d6e94f
**Tree**: clean
**Shell**: /bin/sh
**Result**: 67 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_power.py::test_sem_cache_chama_api_e_salva PASSED` | pass |
| C2 | `run unit / test_power.py::test_com_cache_nao_usa_rede PASSED` | pass |
| C3 | `run unit / test_power.py::test_colunas_um_dia_por_linha PASSED` | pass |
| C4 | `run unit / test_power.py::test_menos_999_vira_nan PASSED` | pass |
| C5 | `run unit / test_power.py::test_falha_sem_cache_erro_fonte PASSED` | pass |
| C6 | `run unit / test_power.py::test_cache_invalido_busca_de_novo PASSED` | pass |
| C7 | `run unit / test_cache.py::test_gravacao_atomica PASSED` | pass |
| C8 | `run unit / test_power.py::test_ponto_invalido_sem_rede PASSED` | pass |
| C9 | `run unit / test_solo.py::test_soilgrids_0_30cm_e_cache PASSED` | pass |
| C10 | `run unit / test_solo.py::test_falha_usa_padrao PASSED` | pass |
| C11 | `run unit / test_pais.py::test_pais_e_hemisferio PASSED` | pass |
| C12 | `run unit / test_pais.py::test_fora_de_pais_iso2_none PASSED` | pass |
| C13 | `run unit / test_solo.py::test_log_requisicoes_power_e_solo PASSED` | pass |
| C14 | `run unit / test_clima.py::test_medias_por_periodo PASSED` | pass |
| C15 | `run unit / test_clima.py::test_inicio_da_estacao PASSED` | pass |
| C16 | `run unit / test_clima.py::test_fim_da_estacao PASSED` | pass |
| C17 | `run unit / test_clima.py::test_conta_veranicos PASSED` | pass |
| C18 | `run unit / test_clima.py::test_anos_sem_estacao PASSED` | pass |
| C19 | `run unit / test_clima.py::test_modo_anual PASSED` | pass |
| C20 | `run unit / test_clima.py::test_resumo_no_idioma PASSED` | pass |
| C21 | `run unit / test_modelo.py::test_simula_1995_a_2024 PASSED` | pass |
| C22 | `run unit / test_balanco.py::test_et0_penman_monteith PASSED` | pass |
| C23 | `run unit / test_balanco.py::test_kc_por_fase PASSED` | pass |
| C24 | `run unit / test_balanco.py::test_balanco_ks_e_deplecao_inicial PASSED` | pass |
| C25 | `run unit / test_balanco.py::test_perda_fao33_limitada PASSED` | pass |
| C26 | `run unit / test_balanco.py::test_quebra_acima_de_20 PASSED` | pass |
| C27 | `run unit / test_modelo.py::test_risco_e_anos_quebra PASSED` | pass |
| C28 | `run unit / test_modelo.py::test_nota_e_ordenacao PASSED` | pass |
| C29 | `run unit / test_modelo.py::test_sem_retorno_reescala_pesos PASSED` | pass |
| C30 | `run unit / test_modelo.py::test_explicacao_antes_e_depois PASSED` | pass |
| C31 | `run unit / test_validacao.py::test_pesos_invalidos PASSED` | pass |
| C32 | `run unit / test_validacao.py::test_pesos_reescalados PASSED` | pass |
| C33 | `run unit / test_validacao.py::test_data_mmdd_invalida PASSED` | pass |
| C34 | `run unit / test_modelo.py::test_cultura_sem_parametros_ignorada PASSED` | pass |
| C35 | `run unit / test_modelo.py::test_formato_saida_ranking PASSED` | pass |
| C36 | `run integ / test_demo.py::test_ranking_menos_de_5s PASSED` | pass |
| C37 | `run unit / test_contexto.py::test_campos PASSED` | pass |
| C38 | `run unit / test_contexto.py::test_nivel_pais PASSED` | pass |
| C39 | `run unit / test_contexto.py::test_nivel_clima PASSED` | pass |
| C40 | `run unit / test_contexto.py::test_classe_climatica PASSED` | pass |
| C41 | `run unit / test_contexto.py::test_fontes PASSED` | pass |
| C42 | `run unit / test_contexto.py::test_fora_de_terra PASSED` | pass |
| C43 | `run unit / test_modelo.py::test_planos_combinacoes_max_5 PASSED` | pass |
| C44 | `run unit / test_modelo.py::test_planos_janelas_3_anos PASSED` | pass |
| C45 | `run unit / test_modelo.py::test_planos_nota_solo PASSED` | pass |
| C46 | `run unit / test_modelo.py::test_planos_inclui_atual PASSED` | pass |
| C47 | `run unit / test_modelo.py::test_planos_top3_mais_atual PASSED` | pass |
| C48 | `run unit / test_modelo.py::test_planos_explicacao_vs_atual PASSED` | pass |
| C49 | `run unit / test_modelo.py::test_planos_historico_invalido PASSED` | pass |
| C50 | `run integ / test_demo.py::test_planos_menos_de_10s PASSED` | pass |
| C51 | `run unit / test_clima.py::test_janela_decendios PASSED` | pass |
| C52 | `run unit / test_clima.py::test_janela_frio PASSED` | pass |
| C53 | `run unit / test_clima.py::test_janela_fim_seguro PASSED` | pass |
| C54 | `run unit / test_clima.py::test_janela_sem_data_segura PASSED` | pass |
| C55 | `run unit / test_modelo.py::test_retorno_faostat PASSED` | pass |
| C56 | `run unit / test_modelo.py::test_sem_linha_retorno_none PASSED` | pass |
| C57 | `run unit / test_contexto.py::test_adaptador_brasil_municipal PASSED` | pass |
| C58 | `run unit / test_textos.py::test_idioma_desconhecido_usa_en PASSED` | pass |
| C59 | `run unit / test_balanco.py::test_nan_chuva_zero_temp_interpolada PASSED` | pass |
| C60 | `run unit / test_balanco.py::test_ciclo_cruza_o_ano PASSED` | pass |
| C61 | `run unit / test_clima.py::test_chuva_por_ano PASSED` | pass |
| C62 | `run unit / test_clima.py::test_temporada_incompleta_fora_das_medias PASSED` | pass |
| C63 | `run unit / test_modelo.py::test_marca_preliminar_quando_nao_validada PASSED` | pass |
| C64 | `run unit / test_modelo.py::test_planos_semeadura_padrao_inicio_das_chuvas PASSED` | pass |
| C65 | `run unit / test_modelo.py::test_planos_historico_com_cultura_sem_parametros PASSED` | pass |
| Build | `.venv/bin/python -m compileall -q core app.py mcp_server.py bot.py` | pass |
| Build | `.venv/bin/ruff check .` | pass |

## Output

`Run unit` - exit 0

```
tests/unit/test_power.py::test_menos_999_vira_nan PASSED                 [ 84%]
tests/unit/test_power.py::test_falha_sem_cache_erro_fonte PASSED         [ 85%]
tests/unit/test_power.py::test_cache_invalido_busca_de_novo PASSED       [ 87%]
tests/unit/test_power.py::test_ponto_invalido_sem_rede PASSED            [ 88%]
tests/unit/test_solo.py::test_soilgrids_0_30cm_e_cache PASSED            [ 89%]
tests/unit/test_solo.py::test_falha_usa_padrao PASSED                    [ 91%]
tests/unit/test_solo.py::test_log_requisicoes_power_e_solo PASSED        [ 92%]
tests/unit/test_textos.py::test_mesmas_chaves_nos_3_idiomas PASSED       [ 93%]
tests/unit/test_textos.py::test_idioma_desconhecido_usa_en PASSED        [ 94%]
tests/unit/test_validacao.py::test_ponto_fora_do_intervalo PASSED        [ 96%]
tests/unit/test_validacao.py::test_data_mmdd_invalida PASSED             [ 97%]
tests/unit/test_validacao.py::test_pesos_invalidos PASSED                [ 98%]
tests/unit/test_validacao.py::test_pesos_reescalados PASSED              [100%]

============================== 78 passed in 2.22s ==============================
```

`Run integ` - exit 0

```
rootdir: /home/nicman/Desktop/Projeto Nasa
plugins: anyio-4.16.0
collecting ... collected 9 items

tests/integracao/test_demo.py::test_ranking_menos_de_5s[Rio Verde] PASSED [ 11%]
tests/integracao/test_demo.py::test_ranking_menos_de_5s[Nakuru] PASSED   [ 22%]
tests/integracao/test_demo.py::test_ranking_menos_de_5s[Ludhiana] PASSED [ 33%]
tests/integracao/test_demo.py::test_ranking_menos_de_5s[Ames] PASSED     [ 44%]
tests/integracao/test_demo.py::test_planos_menos_de_10s[Rio Verde] PASSED [ 55%]
tests/integracao/test_demo.py::test_planos_menos_de_10s[Nakuru] PASSED   [ 66%]
tests/integracao/test_demo.py::test_planos_menos_de_10s[Ludhiana] PASSED [ 77%]
tests/integracao/test_demo.py::test_planos_menos_de_10s[Ames] PASSED     [ 88%]
tests/integracao/test_demo.py::test_rio_verde_milho_mais_arriscado_que_sorgo PASSED [100%]

============================== 9 passed in 9.20s ===============================
```
