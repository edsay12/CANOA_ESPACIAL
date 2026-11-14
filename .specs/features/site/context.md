# Site Context

**Gathered:** 2026-11-14
**Spec:** `.specs/features/site/spec.md`
**Status:** Ready for design

---

## Feature Boundary

O site Streamlit (`app.py`) que deixa qualquer pessoa escolher um ponto no mapa (ou um dos 4 pontos da demo) e ver, a partir do motor, como o clima mudou ali, quais culturas plantar numa data e quais planos de rotação de 3 anos são melhores — com as fontes à vista e em PT, EN ou ES. Não calcula nada: todo número vem do motor (AD-004).

---

## Implementation Decisions

### Processo do time
- Especificar todas as features primeiro; depois cada pessoa implementa a sua parte. — user: "lembrando que vamos especificar primeiro e depois cada um do time vai especificar"

### Wireframe
- Ainda não existe: a spec define comportamentos e estados, não layout. — user: "Ainda não existe (Recommended)"

### Abertura do site
- Abre com mapa-múndi, nenhum ponto selecionado, mensagem para clicar ou escolher um exemplo, e os 4 botões da demo. — user: "Mapa-múndi + 4 botões da demo (Recommended)"

### Telas
- Notebook (1366×768) e celular (390 px de largura). — user: "Notebook e celular (Recommended)"

### Acesso
- Público, sem login. — user: "Qualquer pessoa, sem login (Recommended)"

### Herdado de features anteriores
- Idiomas PT, EN, ES (motor context: user "PT, EN e espanhol").
- Pontos da demo: Rio Verde, Nakuru, Ludhiana, Ames (motor context).

### Organização do código
- `app.py` fino + módulos puros em `web/` (textos, pontos, serviço, apresentação) testados com pytest; gestos testados com o `AppTest` do Streamlit; clique no mapa testado pelo estado da sessão. — user: "app.py fino + módulos puros (Recommended)"

### Agent's Discretion
- Textos exatos das mensagens de estado (vazio, carregando, erro) — propostos na spec para a Cecilia ajustar.

---

## Specific References

- Notion: Guia do Kaue e Guia da Cecilia (estrutura de abas, barra lateral, cards).

---

## Deferred Ideas

- Gráfico extra de SMAP/NDVI.
- Chave "Hoje / 2040" (CMIP6).
- Exportar ficha em PDF.
