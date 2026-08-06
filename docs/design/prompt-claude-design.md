# Prompt pro Claude Design — layout do painel (v1)

> Cole tudo abaixo da linha no claude.ai/design. Os números de exemplo são dados
> reais coletados em 06/08/2026 — use-os literalmente nos mocks pra manter o
> realismo. Depois de iterar no resultado, o design system volta pro repositório
> via `/design-sync` no Claude Code.

---

Crie o layout de um **painel público de dados em tempo real da cidade do Rio de Janeiro**. É um produto web aberto (sem login), em **português brasileiro**, que responde à pergunta: *"como está a cidade agora, e o que isso significa pra quem vive nela?"*

## Contexto do produto

- Agregamos dezenas de fontes de dados abertos da cidade: chuva (33 pluviômetros oficiais), radar meteorológico, estágio operacional do Centro de Operações (COR), GPS de ~6.000 ônibus e BRTs em tempo real, nível de rios, qualidade do ar (28 estações), focos de queimada, previsão do tempo e do mar, e mais fontes chegando (metrô, jogos no Maracanã, balneabilidade das praias, ocorrências de segurança).
- Três diferenciais que o design precisa servir: **(1) memória** — podemos dizer "choveu mais em 3 horas do que a média do mês inteiro" no momento em que acontece; **(2) planejado × realizado** — cruzamos o GPS da frota com a tabela oficial de horários e detectamos linha de ônibus que parou de circular; **(3) transparência** — toda informação exibe a fonte e o horário da leitura.

## Públicos e tom

1. **Imprensa** (o mais importante): precisa de números prontos pra citar e de links que reproduzem exatamente o recorte que ela está vendo.
2. **Cidadão comum**: quer resposta rápida ("vai chover?", "o ônibus tá rodando?"), não exploração de dados.
3. **Comunidade técnica**: avalia a credibilidade pelo rigor (fontes, timestamps, honestidade sobre falhas).

Tom visual: **sóbrio, confiável e legível por leigos**. Nem "sala de comando militar" (sem verde-radar, sem grids de scanline, sem estética de filme de guerra), nem infantil/gamificado. Referência de sensação: a seriedade de um serviço público bem feito com a nitidez de um bom site de jornalismo de dados. Conceito da identidade: **"monitor de sinais vitais da cidade"** — pulso, sparkline, sinal vivo.

**Nome e logo ainda não existem.** Não crie logo, não crie wordmark, não invente nome: no lugar da marca, reserve um espaço vazio de ~140×28 px no header (pode marcar com um retângulo pontilhado discreto "marca"). Todo o resto do design system abaixo é definitivo.

## Design system de partida (tokens obrigatórios)

Use exatamente estes valores — eles vêm da identidade já aprovada do projeto e as paletas de dados foram validadas por contraste e daltonismo sobre a superfície escura.

**Cores de marca**
- Azul profundo `#004A80` — cor institucional. Uso pontual: momentos de destaque de marca, fundos de bloco hero, estados selecionados. **Não** é o fundo da página.
- Ciano `#00C0F3` — o "sinal vivo". Reservado pra: indicador "ao vivo" (dot pulsante), links/ações, valor em destaque no cartão de memória. Usar com parcimônia — é o que faz o painel parecer vivo; se estiver em tudo, não destaca nada.

**Superfícies e texto (tema escuro, o padrão)**
- Fundo da página `#0b0e13` · cartão `#14181f` · cartão elevado/hover `#1a212b` · borda `#242c38`
- Texto primário `#e8eaed` · secundário `#9aa4ad` · desabilitado `#5b6570`
- Números sempre com algarismos tabulares.

**Severidade 1–5 (escala de status, espelha os estágios do COR)** — cada badge SEMPRE com número e ícone, nunca cor sozinha:
- 1 Normalidade `#3fa96b` · 2 Mobilização `#ad8d2c` · 3 Atenção `#c2662a` · 4 Alerta `#cd4048` · 5 Crise `#9b52d6`

**Séries de gráfico (paleta categórica, ordem FIXA — nunca reciclar nem repintar ao filtrar)**
1. `#149cc6` (ciano-dado) · 2. `#c08428` (âmbar) · 3. `#8a6adf` (violeta) · 4. `#cf5590` (rosa) · 5. `#649a30` (verde)
Mais de 5 séries: agrupar em "Outros", nunca gerar cor nova. Texto de rótulo/valor usa os tokens de texto, nunca a cor da série.

**Rampa sequencial (magnitude: intensidade de chuva, mapas de calor)** — um matiz, claro→escuro:
`#9bd7ec → #57b7dc → #2c96c4 → #1d7cab → #166490 → #114e75`

**Tipografia** (Google Fonts, todas gratuitas)
- Display e números-síntese: **Space Grotesk** (geométrica com alma de dado, conforme o conceito da identidade)
- Texto e UI: **Inter**
- Timestamps, códigos de estação e selos de fonte: **JetBrains Mono**
- Escala: 12 / 13 / 15 (corpo) / 18 / 24 / 34 / 48 (número-síntese)

**Layout e grid**
- Grid de 12 colunas, largura máxima do conteúdo 1320 px, gutter 24 px, margens laterais 24 px.
- Cartões: raio 14 px, padding 20 px, borda 1 px `#242c38`, sem sombras pesadas (elevação por cor de superfície).
- Spans na home desktop: cartão destaque (o mais severo do momento) = 8 colunas; cartões normais = 4 colunas; cartão de memória = 6 colunas.
- Espaçamento em escala de 4: 4/8/12/16/24/32/48. Breakpoints: 640 (mobile), 1024 (tablet), 1440.
- Gráficos: linhas de 2 px, grid recessivo (borda sutil), tooltips em toda série temporal, legenda presente quando houver 2+ séries.

**Regras de uso da cor** (herdadas da metodologia de dataviz do projeto)
- Cor de status (severidade) nunca vira cor de série de gráfico, e vice-versa.
- Nunca dois eixos y no mesmo gráfico; nunca rainbow em escala de magnitude.
- Estado "fonte degradada" usa o âmbar de severidade 2 + ícone, com texto explicativo.

## Princípios inegociáveis

1. **O painel NÃO é um mapa fullscreen.** A home é uma página de leitura em cartões; o mapa é uma vista dedicada e aparece em miniatura dentro de cartões onde geografia importa.
2. **Priorização por severidade**: o que está anormal sobe e ganha destaque; num dia calmo, a home diz explicitamente que a cidade está normal (calma também é informação).
3. **Rotulagem obrigatória**: todo número, gráfico ou mapa carrega um selo discreto "Fonte: X · há N min". É requisito do produto, não decoração — desenhe um componente elegante e reutilizável pra isso.
4. **Honestidade sobre falhas**: se uma fonte está fora do ar ou com dado velho, o cartão mostra isso claramente (estado "degradado") em vez de esconder ou exibir número obsoleto como se fosse atual.
5. **Todo estado de filtro vive na URL** (a imprensa compartilha o recorte). Indique visualmente que as vistas são compartilháveis (botão "copiar link deste recorte").
6. **Densidade com hierarquia.** A home deve dar a sensação de MUITO dado ao vivo — é um monitor de sinais vitais, e a abundância de leituras é parte da credibilidade e do impacto. Meta concreta: 50+ números visíveis na home sem rolagem no desktop, em camadas (número-síntese grande → linha de métricas secundárias → micro-tabela ou sparkline), mais um ticker e um feed correndo. O que separa isso de "poluído": hierarquia tipográfica rígida, alinhamento em grid, e o ciano reservado ao que está vivo. Denso, não militar: nada de scanlines, HUDs ou verde-radar.

## Escala de severidade (usada em todo o produto)

Espelha os 5 estágios operacionais oficiais da cidade — o público do Rio já conhece:
- **1 Normalidade** (verde), **2 Mobilização** (amarelo), **3 Atenção** (laranja), **4 Alerta** (vermelho), **5 Crise** (roxo/magenta escuro).
Crie tokens de cor pros 5 níveis funcionando sobre fundo escuro, com versão acessível (não depender só de cor: ícone/números junto).

## Telas a gerar

### Tela 1 — Home (desktop e mobile)

**Navegação**: Agora · Mapa · Análises · Status. ("Análises" é a camada de aprofundamento — antigo "Painéis".)

**Cabeçalho de estado** (topo, sempre visível): estágio atual da cidade em destaque + um resumo de uma linha. Mock: "**Estágio 1 — Normalidade** · A cidade opera normalmente. Sem chuva nas últimas 24h." Fonte: COR · há 3 min.

**Ticker de leituras** (faixa fina logo abaixo do cabeçalho, rolagem horizontal contínua e pausável): leituras ao vivo intercaladas de todas as fontes, em JetBrains Mono. Mock: `COPACABANA 0,0mm · PM2.5 IRAJÁ 13,3 · RIO TIJUCA 65cm ▬ · 4.212 VEÍCULOS ▲ · ONDAS 1,4m · METRÔ L1 NORMAL · SDU 12 POUSOS/H · ESTÁGIO 1`. É o elemento que faz a página parecer um organismo vivo.

**Feed "agora na cidade"** (coluna direita no desktop, ~320 px): lista cronológica dos últimos eventos/transições de todas as fontes, com badge de severidade e idade. Mock: "14:28 · linha 232 voltou a circular", "14:11 · PM10 subiu pra moderado em Bangu", "13:47 · COR: bolsão d'água em Jacarepaguá — resolvido 14:20", "12:40 · 2 focos de calor na Região Metropolitana (fora do município)". O feed rola independente.

**Grade de cartões temáticos** (a ordem muda conforme severidade; num dia calmo):

O painel cobre o escopo COMPLETO de lançamento — inclua TODOS os cartões abaixo, mesmo os de fonte que ainda entra (desenhe-os com dados de exemplo normais, não como "em breve"):

1. **Chuva e água** — número-síntese: "0,0 mm na última hora (todas as 33 estações)". Mini-mapa com o radar sobreposto (mock: 2 ecos verdes fracos na serra, cidade limpa). Sparkline de chuva 24h (flat em zero). Linha secundária: "Rios: Tijuca 65 cm — estável · Acari, Maracanã, Faria-Timbó ok". Selo: Alerta Rio + ANA · há 4 min.
2. **Mobilidade** — número-síntese grande: "**4.200 veículos em circulação**" com detalhe "3.642 ônibus + 558 BRT · 96% das linhas planejadas ativas". Um aviso de exemplo do detector: "⚠ 3 linhas sem circular há 40+ min: 232, SV790, 863". Mini-mapa de pontos da frota. Linha do metrô: "L1 ● L2 ● L4 ● operação normal". Selo: SMTR + MetrôRio · ao vivo (1 min).
3. **Segurança** — número-síntese: "**3 ocorrências de tiro** nas últimas 24 h" com detalhe "Zona Norte 2 · Zona Oeste 1 · nenhuma nas últimas 6 h". Mini-mapa H3 (hexágonos discretos, sem pino sensacionalista) + linha de contexto mensal: "julho: 214 ocorrências no estado — taxa 1,24/100 mil (ISP)". Selo: Fogo Cruzado + ISP · há 12 min. IMPORTANTE: tratamento visual sério e contido — é dado sensível; nada de vermelho piscante.
4. **Trânsito** — "Velocidade média dos corredores: **31 km/h** · fluxo livre 42". Micro-tabela dos 4 piores corredores agora (Av. Brasil 18 km/h ▼, Aterro 51 ▲, Linha Amarela 24, Av. das Américas 27). Derivado da nossa frota + TomTom. Selo: SMTR/TomTom · há 5 min.
5. **Previsão** — hoje à tarde: "**31 °C**, sem chuva à vista · umidade 58% · vento 18 km/h SE". Faixa horária das próximas 12 h (mini barras de temperatura + gotas de probabilidade de chuva). Selo: Open-Meteo · rodada de 14h.
6. **Qualidade do ar** — "**Boa** · PM2.5 máx 16,7 µg/m³ (Campinho)". Lista das 3 piores estações com barrinhas + "28 estações reportando". Selo: OpenAQ · há 20 min.
7. **Mar e praias** — "Ondas de **1,4 m**, período 9 s · mar calmo" + balneabilidade: "Praias: 14 próprias · 3 impróprias (Botafogo, Flamengo, Ramos)". Selo: Open-Meteo Marine + INEA · boletim de 04/08.
8. **Céu** — "**14 aeronaves** sobre a cidade agora · SDU 12 pousos/h · GIG 21". Linha secundária: "pontualidade julho: 87% (VRA/ANAC)". Selo: adsb.lol · ao vivo.
9. **Queimadas** — "0 focos no município nas últimas 3 h · 3 na Região Metropolitana em 24 h". Selo: INPE · há 8 min.
10. **Cidade viva** — agenda + serviços: "Sáb 19:30 · Flamengo × Vitória, Maracanã (esquema especial de trânsito)" + "Águas do Rio: manutenção programada em Irajá, qui 22h–5h". Selo: TheSportsDB + Águas do Rio.
11. **Cartão de memória (Tese 2)** — um cartão editorial que contextualiza: "Agosto até agora: 12 mm de chuva — 34% da média histórica do mês". Este cartão é o diferencial do produto; dê a ele um tratamento visual próprio (citação de dado, tipografia maior, botão "copiar dado citável").
12. **Navios (AIS)** — exemplo do estado degradado: fonte instável, mostrando última leitura válida com aviso honesto.

**Rodapé**: link pra página de status das fontes ("12 de 12 fontes operando normalmente ●"), metodologia (placeholder), e nota de licença dos dados.

**Versão mobile**: os cartões empilham; o cabeçalho de estado vira uma barra compacta fixa; navegação inferior com 4 itens (Agora, Mapa, Análises, Status). O ticker permanece (uma linha, rolagem contínua); o feed vira uma aba dentro de "Agora".

### Tela 2 — Vista Mapa (`/mapa`)

Mapa escuro da cidade ocupando a área principal, com:
- **Painel de camadas** (lateral no desktop, sheet inferior no mobile): ligar/desligar Frota, Radar, Chuva por estação, Eventos, Qualidade do ar. Cada camada com seu selo de fonte.
- **Linha do tempo** no rodapé do mapa pra animar o radar (últimos 40 min, botão play).
- **Chips de filtro** no topo: bairro/zona, janela de tempo (3h/24h), severidade ("só o anormal").
- Botão "copiar link deste recorte".
- Um pino de exemplo aberto (popover): evento com título, severidade, horário, fonte.

### Tela 3 — Status das fontes (`/status`)

Tabela/lista pública de todas as fontes: nome, órgão, estado atual (online/degradada/fora/congelada com os ícones da escala), última leitura, uptime 30 dias (barrinha estilo status page). Mock: 11 online + 1 degradada ("Navios (AIS) — instável desde 05/08"). É a página da transparência — visual de status page séria.

### Tela 4 — Índice de Análises (`/analises`)

A porta de entrada da camada de aprofundamento: grade com um bloco por tema (os mesmos 10 temas dos cartões da home), cada um com título, número-síntese atual e um resumo do que a análise oferece ("séries desde 1997", "planejado × realizado por linha", "taxa /100 mil por região"). Deixe claro pelo design que aqui é onde mora o histórico e o contexto — a home é o agora, as Análises são a memória.

### Tela 5 — Detalhe de uma Análise (exemplo: Chuva e água)

Página aprofundada: gráfico de série temporal grande (chuva por hora, 24h–30 dias, com anotações de eventos: faixa vermelha quando a cidade entrou em Estágio 3), tabela das 33 estações ordenável, mapa das estações, e o bloco de contexto histórico ("percentil 95 pra agosto"). Seletor de período e comparação com a média histórica.

## Componentes que preciso que existam como peças reutilizáveis

- **Selo de fonte** (fonte + idade do dado, com estado: fresco / velho / fora).
- **Número-síntese** (valor grande + rótulo + variação/comparação histórica).
- **Cartão temático** (header com título e severidade, corpo flexível, selo no rodapé).
- **Sparkline** e **mini gráfico de barras horárias**.
- **Badge de severidade 1–5**.
- **Mini-mapa** (moldura padrão pra frota/radar dentro de cartões).
- **Chip de filtro** (ativo/inativo) e **botão "copiar link"**.
- **Banner de estado degradado** (quando uma fonte do cartão está fora).
- **Ticker de leituras** (item mono + separador, com variação ▲▼▬).
- **Item de feed** (timestamp mono + badge de severidade + texto de uma linha).

## Estados a desenhar

- Dia calmo (o mock principal acima) e **dia de crise** (uma variação da home com Estágio 4: cabeçalho vermelho, cartão de chuva no topo com 45 mm/h em Jacarepaguá, radar carregado, 14 linhas de ônibus parada) — só a home nessa segunda condição, pra validar que a hierarquia por severidade funciona.
- Cartão em carregamento (skeleton) e cartão com fonte fora do ar.

## Entregáveis

Home (desktop + mobile, dia calmo), Home dia de crise (desktop), Vista Mapa (desktop), Índice de Análises (desktop), Detalhe Chuva (desktop), Status (desktop) — e o inventário de componentes/tokens (cores, tipografia, espaçamentos) organizado pra virar design system.
