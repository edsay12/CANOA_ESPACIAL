# 🛰️ Field Shift — Adaptando Fazendas com Dados da NASA

**NASA Space Apps Challenge 2026 · Desafio 06/14** · 14 e 15/11/2026
Dificuldade: Intermediário · Avançado · Temas: Arte & Multimídia, Ciências da Terra, Software & Código

🔗 Página oficial: https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/?tab=details

---

## 📋 Enunciado oficial

> Agricultores no mundo todo enfrentam temperaturas em mudança, padrões de chuva alterados, escassez de água, eventos climáticos extremos e piora da saúde do solo. Essas pressões dificultam escolher rotações de culturas que protejam os campos, conservem água e sustentem a resiliência de longo prazo. O desafio é criar uma ferramenta de apoio à decisão que use observações da Terra da NASA, junto com informações locais de solo, características das culturas e prioridades do agricultor, para ajudá-lo a explorar estratégias de rotação que fortaleçam a saúde do solo e adaptem … *(colar o restante do texto oficial)*

### ⚠️ Regra obrigatória

**O projeto precisa usar pelo menos um dado público da NASA para se classificar para a fase global.** Também podemos usar dados de outras agências e fontes públicas.

---

## 🤔 Por que este problema importa

1. **O clima está mudando o que dá para plantar onde.** As janelas de plantio mudam, e secas relâmpago e ondas de calor ficam mais frequentes. Uma rotação que funcionou por 20 anos pode deixar de funcionar.
2. **Monocultura desgasta o solo.** A rotação repõe nutrientes, quebra o ciclo de pragas e guarda mais água. Mas é uma decisão de **vários anos**, e errar custa caro.
3. **O dado existe, mas não chega ao agricultor.** Os satélites medem umidade, vegetação e estresse hídrico, e quase nenhum produtor consegue usar isso direto. **O valor está em transformar esses dados numa decisão.**
4. **Cada agricultor tem prioridades diferentes** (lucro, risco, água, solo). A ferramenta precisa **mostrar as vantagens e desvantagens de cada opção e explicar o porquê**, não só entregar uma resposta.

---

## 🎯 Nossa proposta (rascunho do MVP)

O usuário **escolhe um ponto no mapa e informa as prioridades**. A ferramenta **compara 2 ou 3 rotações** e dá a cada uma um **score explicável**, por exemplo: risco hídrico, saúde do solo e retorno.

Exemplo de explicação: *"Milho safrinha tem 40% de risco de déficit hídrico em março, segundo 20 anos de dados do NASA POWER."*

- [ ] Definir a região-alvo e o perfil de produtor (sugestão: soja + milho safrinha no Cerrado, ou agricultura familiar no semiárido)
- [ ] Escrever o problema em uma frase: "O produtor X não sabe se deve rotacionar para Y por causa do risco Z"
- [ ] Escolher as rotações candidatas
- [ ] Escolher os 3 critérios do score

---

## 🗓️ Fases do hackathon

| Fase | Duração | O que entregar |
|---|---|---|
| 0 · Alinhamento | ~1h | Ler o enunciado completo, os critérios de avaliação e a lista de entregáveis. Escolher a região |
| 1 · Definir o problema | ~2h | Frase do problema, rotações candidatas, critérios |
| 2 · Dados | ~6h | Começar só com o NASA POWER. Entram SMAP/NDVI se der tempo |
| 3 · MVP | ~16h | Mapa + prioridades → comparação com score explicável |
| 4 · Narrativa e entrega | ~8h | Vídeo, slides, README listando os dados NASA usados, ensaio do pitch |
| 5 · Folga | restante | Corrigir bugs e dormir |

### ✅ Checklist de entrega

- [ ] Projeto submetido na plataforma Space Apps
- [ ] Repositório público com README
- [ ] README lista **todos os dados da NASA** usados
- [ ] Vídeo/demo
- [ ] Slides
- [ ] Pitch ensaiado

---

## 👥 Equipe e responsabilidades

| Pessoa | Papel | Tarefa atual |
|---|---|---|
| Edvan | Líder | |
| | Dados / Python | |
| | Front-end / Mapa | |
| | Design / Pitch | |
| | Agronomia / Pesquisa | |

---

## 🛰️ Dados da NASA

| Dado | Para que serve | Link |
|---|---|---|
| **NASA POWER** ⭐ começar aqui | Clima diário desde 1981 (temperatura, chuva, radiação, umidade do solo). Sem cadastro | https://power.larc.nasa.gov/data-access-viewer/ |
| NASA POWER: docs da API | Referência dos endpoints e parâmetros | https://power.larc.nasa.gov/docs/ |
| **AppEEARS** ⭐ | Extrai séries de MODIS, SMAP, ECOSTRESS e HLS para um ponto ou área, sem processar imagem | https://appeears.earthdatacloud.nasa.gov/ |
| SMAP | Umidade do solo | https://smap.jpl.nasa.gov/data/ |
| GPM IMERG | Chuva por satélite | https://gpm.nasa.gov/data/imerg |
| ECOSTRESS | Evapotranspiração e estresse hídrico | https://ecostress.jpl.nasa.gov/data |
| HLS (Landsat + Sentinel) | NDVI a 30 m, histórico do talhão | https://hls.gsfc.nasa.gov/ |
| MODIS | NDVI e cobertura do solo | https://modis.gsfc.nasa.gov/data/ |
| Worldview | Ver imagens de satélite no navegador | https://worldview.earthdata.nasa.gov/ |
| Earthdata (login) | Cadastro necessário para SMAP, AppEEARS etc. | https://urs.earthdata.nasa.gov/ |

### NASA POWER: guia rápido

- **Comunidade:** `AG` (Agroclimatology)
- **Resolução:** cerca de 50 km. Descreve o clima da **região**, não do talhão
- **Parâmetros úteis:** `T2M`, `T2M_MAX`, `T2M_MIN` (temperatura), `PRECTOTCORR` (chuva), `RH2M` (umidade do ar), `ALLSKY_SFC_SW_DWN` (radiação), `WS2M` (vento), `GWETROOT` / `GWETTOP` (umidade do solo)

Exemplo de chamada à API:

```
https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M_MAX,T2M_MIN,PRECTOTCORR,GWETROOT&community=AG&latitude=-15.8&longitude=-47.9&start=20000101&end=20241231&format=JSON
```

```python
import requests

params = {
    "parameters": "T2M_MAX,T2M_MIN,PRECTOTCORR,GWETROOT",
    "community": "AG",
    "latitude": -15.8, "longitude": -47.9,
    "start": "20000101", "end": "20241231",
    "format": "JSON",
}
data = requests.get("https://power.larc.nasa.gov/api/temporal/daily/point",
                    params=params, timeout=60).json()
chuva = data["properties"]["parameter"]["PRECTOTCORR"]  # {"20000101": 3.2, ...}
```

---

## 🌍 Outras agências espaciais e climáticas

| Agência | O que oferece | Link |
|---|---|---|
| 🇪🇺 ESA / Copernicus | Satélites Sentinel | https://dataspace.copernicus.eu/ |
| 🇺🇸 NOAA | Clima, oceanos, incêndios, furacões | https://www.ncei.noaa.gov/ |
| 🇺🇸 USGS | Topografia, mapas, Landsat | https://earthexplorer.usgs.gov/ |
| 🇯🇵 JAXA | Observação e radar (GPM, ALOS) | https://gportal.jaxa.jp/ |
| … | *(colar o restante da lista)* | |

## 🌱 Solo, culturas e Brasil

| Fonte | O que oferece | Link |
|---|---|---|
| SoilGrids | Solo global: textura, pH, matéria orgânica | https://soilgrids.org/ |
| FAO GAEZ | Exigências e aptidão das culturas | https://gaez.fao.org/ |
| MapBiomas | Uso do solo no Brasil, ano a ano | https://brasil.mapbiomas.org/ |
| Embrapa GeoInfo | Mapas de solo do Brasil | https://geoinfo.dados.embrapa.br/ |
| INMET | Estações meteorológicas no Brasil | https://portal.inmet.gov.br/ |
| ZARC (MAPA) | Zoneamento de risco climático por cultura | https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-agricola-de-risco-climatico |

---

## 🎙️ Mentorias (Google Meet · 14 e 15/11)

Mentorias curtas de 15 a 20 min. Plantão de apoio no canal 📡┆houston-preciso-de-ajuda-técn…

⭐ = mais relevante para o nosso desafio

**☀️ Manhã**

- 09:00–09:20 · Icaro Costa — Software para saúde e dados
- 09:30–09:50 · João Ataíde — Modelagem matemática e geoespacial ⭐
- 10:00–10:20 · Luciana Delavec — Ferramentas digitais e IA
- 10:30–10:50 · Vitor Lima — Georreferenciamento e dados ⭐
- 11:00–11:20 · Maria Efigênia Farias — Da Terra ao Espaço: Ciência, Dados e Inovação para os Desafios do Planeta ⭐
- 11:30–11:50 · Juliana Gomes — Astronomia e Exploração Espacial

🍽️ Almoço: 11:50–13:00

**🌤️ Tarde e noite**

- 13:00–13:20 · Eder Leão — Análise de dados e sustentabilidade ⭐
- 13:30–13:50 · Tiag… *(colar o restante da escala)*

---

## ⚠️ Avisos técnicos

- **Rede corporativa:** se aparecer o erro "unable to get local issuer certificate", **não desligue a verificação SSL**. Use outra rede (4G, rede do evento) ou instale o certificado raiz da empresa.
- **SMAP e AppEEARS exigem login no Earthdata.** Façam o cadastro cedo, porque a ativação pode demorar.
