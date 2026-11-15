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

## Publicar o MCP em HTTPS para a demo

Configure um `MCP_TOKEN` secreto no `.env` e mantenha o MCP em `127.0.0.1`. Com o `cloudflared` instalado, inicie o túnel para a porta `MCP_PORT` do seu `.env`.

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Copie o endereço HTTPS gerado para `MCP_PUBLIC_URL` com o sufixo `/mcp`. Para um Quick Tunnel, defina `MCP_STATELESS_HTTP=true` para responder em JSON pelo Streamable HTTP. Em outro terminal, na raiz do projeto, inicie o servidor.

```powershell
.venv/Scripts/python.exe mcp_server.py
```

A Groq usa `MCP_PUBLIC_URL` para acessar as ferramentas com `Authorization: Bearer <MCP_TOKEN>`. Para verificar o endpoint, faça `initialize`, `tools/list` e uma chamada a `info_cultura` com esse cabeçalho. Sem token, o endpoint responde `401`. O endereço do Quick Tunnel muda a cada nova execução. Atualize `MCP_PUBLIC_URL` e reinicie o servidor e o bot quando isso acontecer. [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)

## Dados da NASA usados

- [NASA POWER](https://power.larc.nasa.gov/) — clima diário (chuva, temperatura, radiação, umidade do solo)
