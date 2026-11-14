# Motor Context

**Gathered:** 2026-11-14
**Spec:** `.specs/features/motor/spec.md`
**Status:** Ready for design

---

## Feature Boundary

O núcleo Python (`core/`) que, para qualquer ponto do planeta, busca clima (NASA POWER) e solo (SoilGrids), descobre o país, calcula "seu clima mudou", ranqueia culturas para uma safra, monta planos de rotação de 3 anos e estima a janela de plantio. Não tem tela, bot, LLM nem banco de dados.

---

## Implementation Decisions

### Divisão do MVP
- O MVP é especificado em 3 features em ordem: 1) motor, 2) site, 3) bot + MCP. — user: "3 features em ordem (Recommended)"

### Risco e comparação climática
- Uma safra conta como quebra quando a perda estimada (FAO-33) passa de 20%. — user: "Perda >20%; 1995–2009 × 2010–2025 (Recommended)"
- "Seu clima mudou" compara 1995–2009 com 2010–2025. — mesma resposta.

### Pontos da demo
- Rio Verde (GO) -17.80, -50.92 · Nakuru (KE) -0.30, 36.07 · Ludhiana (IN) 30.90, 75.85 · Ames (US) 42.03, -93.62. — user: "Sim, esses 4 (Recommended)"

### Idiomas
- Textos gerados pelo motor (resumo, explicação) em português, inglês e espanhol. — user: "PT, EN e espanhol"

### Abordagem de cálculo
- Implementação própria do FAO-56 simplificado (Kc simples, balanço "balde"), funções puras com pandas/numpy. — user: "Implementação própria FAO-56 simples (Recommended)"

### Testes e build
- pytest com testes de unidade (séries sintéticas, rede simulada) e de integração nos 4 pontos usando o cache versionado. — user: "pytest: unit + integração com cache (Recommended)"
- Lint com ruff no build. — user: "ruff (Recommended)"

### Agent's Discretion
- Detalhes do modelo de balanço hídrico (umidade inicial do solo, classes climáticas, critérios de início/fim das chuvas) — registrados como assumptions na spec para o time corrigir.

### Declined / Undiscussed Gray Areas → Assumptions
- Pesos padrão das prioridades, nome do produto, regra de classe climática: ver Assumptions da spec.

---

## Specific References

- Fórmulas: FAO-56 (Hargreaves eq. 52, Ra eq. 21, balanço hídrico cap. 8), FAO-33 (Ky).
- Arquitetura: página "Arquitetura do MVP" no Notion; decisões AD-001..AD-004 em `.specs/STATE.md`.

---

## Deferred Ideas

- Clima futuro (NEX-GDDP-CMIP6) — feature futura.
- SMAP/MODIS como segunda fonte de satélite — feature futura.
- Alertas de veranico — feature bot + MCP.
