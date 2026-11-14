# Bot Context

**Gathered:** 2026-11-14
**Spec:** `.specs/features/bot/spec.md`
**Status:** Ready for design

---

## Feature Boundary

O bot do Telegram (`bot.py`), o servidor MCP (`mcp_server.py`), o banco SQLite compartilhado (`core/db.py`) e a leitura de clima recente para fotos e alertas. O produtor manda localização, perguntas (texto ou áudio) e fotos; a LLM da Groq entende e chama as ferramentas do motor pelo MCP; o banco liga o bot ao site (pins e botão do Telegram). Os números vêm sempre do motor (AD-004).

---

## Implementation Decisions

### Acesso e limite
- Bot público, 20 mensagens por usuário por hora. — user: "Qualquer um, 20 msgs/hora (Recommended)"

### Retenção de dados
- Fotos e localizações guardadas até o fim do hackathon e apagadas manualmente depois; sem comando /apagar. — user: "Até o fim do hackathon"

### Falha da LLM
- Quando a Groq falha ou estoura o limite, o bot só responde com mensagem de erro. — user: "Só mensagem de erro"

### Segurança do MCP
- O MCP exige `Authorization: Bearer <MCP_TOKEN>`; a Groq envia o cabeçalho na configuração do Remote MCP. — user: "Token secreto no cabeçalho (Recommended)"

### Herdado
- Groq com Remote MCP e plano B por function calling local (AD-002); idiomas pt/en/es (motor); "todo número vem do motor" e "fotos são descritas, não diagnosticadas" (AD-004).
- Processo: especificar tudo primeiro, depois o time implementa.

### Organização
- Dois processos (`mcp_server.py` com `MCPServer` do mcp 2.x + middleware de token via uvicorn, e `bot.py` com python-telegram-bot); regras do bot em `bot_logica/` com funções puras testadas por pytest; `bot.py` só liga os handlers. — user: "2 processos + lógica pura (Recommended)"

### Agent's Discretion
- Horário do job de alertas, intervalo mínimo entre alertas, uma fazenda por chat, texto do aviso de privacidade — registrados como assumptions.

---

## Specific References

- Notion: Guia do Vinicius (prompt do sistema, fluxos), Guia do Nascimento (alertas, áudio), Guia da Cecilia (tom das mensagens).
- `.specs/features/site/spec.md` SITE-32..36 consomem `core/db.py`.

---

## Deferred Ideas

- Comando /apagar (usuário optou por apagar manualmente após o evento).
- Respostas sem LLM quando a Groq cai (usuário optou só por mensagem de erro).
- Resposta em áudio (TTS).
