# STATE

## Decisions

### AD-001
- **Decision**: O produto são dois sistemas — site (Streamlit, mapa) e bot Telegram — sobre o mesmo núcleo Python e o mesmo banco SQLite; o bot acessa o núcleo por um servidor MCP.
- **Reason**: Site para técnico/jurado; Telegram alcança o produtor no campo (Bot API gratuita, localização, foto, áudio, push). MCP deixa a LLM chamar o motor sem lógica duplicada.
- **Trade-off**: Três processos para manter no ar (site, MCP, bot) e uma URL pública para o MCP.
- **Scope**: todo o projeto
- **Date**: 2026-11-14
- **Status**: active

### AD-002
- **Decision**: LLM inicial do bot é a Groq (Responses API com Remote MCP); plano B é function calling local.
- **Reason**: Escolha do time; rápida, compatível com OpenAI, tem Whisper (áudio) e modelo com visão.
- **Trade-off**: Remote MCP da Groq está em beta; nomes de modelos mudam.
- **Scope**: bot.py
- **Date**: 2026-11-14
- **Status**: active

### AD-003
- **Decision**: Sistema mundial em 3 camadas: núcleo global (NASA POWER, SoilGrids, FAO-56), contexto global (país, FAOSTAT) e adaptadores nacionais opcionais (Brasil primeiro). Janela de plantio derivada do clima quando não há dado local.
- **Reason**: Funcionar em qualquer ponto do planeta sem depender de dado nacional.
- **Trade-off**: Precisão menor fora de países com adaptador; janela de plantio é estimativa.
- **Scope**: core/
- **Date**: 2026-11-14
- **Status**: active

### AD-004
- **Decision**: Todo número mostrado ao usuário (site ou bot) vem do núcleo; a LLM só interpreta a pergunta e redige a resposta. Fotos são descritas, nunca diagnosticadas.
- **Reason**: Confiabilidade e honestidade sobre limites (barreira "sintoma × causa").
- **Trade-off**: Bot não responde perguntas fora das ferramentas.
- **Scope**: bot.py, mcp_server.py
- **Date**: 2026-11-14
- **Status**: active

### AD-005
- **Decision**: Nomear novas branches e escrever mensagens de commit em inglês.
- **Reason**: Convenção solicitada pelo usuário para todo o projeto.
- **Trade-off**: O histórico reúne mensagens em português e em inglês.
- **Scope**: branches e commits do projeto
- **Date**: 2026-11-15
- **Status**: active

### AD-006
- **Decision**: O botão de clima permanece visível e desabilitado na primeira entrega do Site, inclusive após selecionar um local.
- **Reason**: À pergunta “Na primeira entrega, o que deve acontecer ao clicar em ‘Ver o que mudou no meu clima’ depois de escolher um local?”, o usuário respondeu “Manter o botão desabilitado até a etapa de clima existir”.
- **Scope**: Primeira entrega do Site, tela “Onde fica sua terra?”
- **Date**: 2026-11-15
- **Status**: active (AD-006)

## Handoff
