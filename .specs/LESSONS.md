# LESSONS - auto-maintained by scripts/lessons.py

> Machine-owned. Do NOT hand-edit. Changes are overwritten on the next `lessons.py` write.
> Canonical state lives in `.specs/lessons.json`. Edit lessons only via the script.
> promote_threshold=2 distinct features · window_days=45 · quarantine_threshold=2

## Confirmed (load these at Plan/Checks)

Corroborated across multiple features. Safe to apply as guidance.

_none_

## Candidates (under observation - do NOT load as guidance yet)

Seen once or not yet corroborated. Tracked, not trusted.

### L-001 - Em testes de interface, fixe os rótulos e as coordenadas esperadas dos locais de demonstração.
- signal: `weak_test` · recurrence: 1 feature(s) · scope: `tests/web` · harmful: 0
- features: site-localizacao
- evidence: C4 (tests/web)
- last seen: 2026-11-15T22:56:53Z

### L-002 - Verifique o texto de cada selo de precisão com a resposta correspondente do motor.
- signal: `weak_test` · recurrence: 1 feature(s) · scope: `tests/web` · harmful: 0
- features: site-localizacao
- evidence: C5 (tests/web)
- last seen: 2026-11-15T22:56:53Z

### L-003 - Ao testar a troca de idioma, confira os textos fixos de cada largura e o estado preservado.
- signal: `weak_test` · recurrence: 1 feature(s) · scope: `tests/web` · harmful: 0
- features: site-localizacao
- evidence: C8 (tests/web)
- last seen: 2026-11-15T22:56:53Z

### L-004 - Em testes de recuperação de uma seleção inválida, use o controle que permite escolher outro ponto.
- signal: `weak_test` · recurrence: 1 feature(s) · scope: `tests/web` · harmful: 0
- features: site-localizacao
- evidence: C10 (tests/web)
- last seen: 2026-11-15T22:56:53Z

### L-005 - Teste o cache de localização com coordenadas brutas diferentes que normalizam para o mesmo ponto.
- signal: `weak_test` · recurrence: 1 feature(s) · scope: `tests/web` · harmful: 0
- features: site-localizacao
- evidence: C12 (tests/web)
- last seen: 2026-11-15T22:56:53Z

## Quarantined (failed when applied - ignore)

A confirmed lesson that recurred alongside failure. Kept for the maintainer to review.

_none_
