# Site — Onde fica sua terra? Design

**Spec**: [Especificação aprovada](spec.md)

## Architecture

- `app.py` monta a abertura em Streamlit e mantém o idioma, o ponto escolhido e o cache do serviço em `st.session_state`. A seleção no mapa e os exemplos alimentam o mesmo estado.
- `web/i18n.py` fornece os textos de desktop e celular em português, inglês e espanhol. `web/pontos.py` fornece os quatro exemplos e normaliza as coordenadas antes da consulta.
- `web/mapa.py` concentra o mapa interativo com Folium e streamlit-folium. O mapa usa a arte de continentes do Figma como camada local. A implementação confere o encaixe da imagem com as coordenadas em marcos conhecidos antes de ligar os cliques ao motor.
- `web/localizacao.py` apresenta o contexto do ponto com o nome do país, as coordenadas e o selo de precisão. O serviço existente consulta o motor e reaproveita o contexto bem-sucedido por ponto na sessão. O painel usa o indicador de carregamento e as mensagens traduzidas de terra firme e indisponibilidade. Uma nova escolha ou tentativa pode substituir o erro.
- Os ícones e a arte do Figma ficam em `assets/site-location/`. Os estilos da abertura seguem as duas referências e mantêm os controles interativos acessíveis. O botão de clima é desabilitado de forma semântica em ambas as larguras.

## Verification

Pytest e AppTest verificam os gestos e as respostas do serviço com dados controlados. A verificação em navegador confere o clique real no mapa, a posição do marcador, o carregamento e a composição a 1366 × 978 e 390 × 1035. As duas capturas originais ficam ao lado das capturas da página em execução.
