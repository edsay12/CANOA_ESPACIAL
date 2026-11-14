# 🛶 Canoa Espacial

NASA Space Apps Challenge 2026 · desafio *Field Shift: Adapting Farms with NASA Data*.

Ferramenta mundial de apoio à decisão de rotação de culturas: simula, com 30 anos de clima do
**NASA POWER**, quais planos de rotação equilibram risco de seca, saúde do solo e retorno, num
site com mapa e num bot do Telegram.

## Estrutura

```
core/            núcleo (sem tela, bot ou LLM)
  power.py solo.py clima.py modelo.py   camada 1 · global
  pais.py global_ctx.py                 camada 2 · contexto global
  adaptadores/brasil.py                 camada 3 · opcional
  contexto.py db.py
data/            culturas.csv, faostat.csv, paises.geojson, mock/, fotos/
cache/           respostas do POWER/SoilGrids (pontos da demo versionados)
assets/          logo e identidade visual
tests/           testes dos critérios de aceite
app.py           site Streamlit
mcp_server.py    servidor MCP
bot.py           bot Telegram (Groq)
.specs/          especificação (spec-driven)
```

## Como rodar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencher as chaves
streamlit run app.py
```

## Dados da NASA usados

- [NASA POWER](https://power.larc.nasa.gov/) — clima diário (chuva, temperatura, radiação, umidade do solo)
