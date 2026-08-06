# riolive — design system (painel público de dados do Rio)

Painel web público, tema escuro, pt-BR. Conceito: **monitor de sinais vitais da cidade** — denso de dados ao vivo, com hierarquia rígida. Sóbrio e acessível a leigos; nunca estética militar (sem scanlines/HUD/verde-radar). Nome e logo em definição: **não criar marca**; reservar espaço vazio ~140×28 no header.

## Cores

**Marca**: azul institucional `#004A80` (uso pontual, nunca fundo de página) · ciano `#00C0F3` = "sinal vivo", reservado a indicador ao-vivo, links/ações e destaque — com parcimônia.

**Superfícies**: página `#0b0e13` · cartão `#14181f` · elevado/hover `#1a212b` · borda `#242c38` (1px).
**Texto**: primário `#e8eaed` · secundário `#9aa4ad` · desabilitado `#5b6570`. Números sempre tabulares.

**Severidade 1–5** (escala de status; espelha os estágios do COR; SEMPRE número+ícone junto, nunca cor sozinha):
1 Normalidade `#3fa96b` · 2 Mobilização `#ad8d2c` · 3 Atenção `#c2662a` · 4 Alerta `#cd4048` · 5 Crise `#9b52d6`.

**Séries de gráfico** (categórica, ordem FIXA, nunca reciclar; 6+ séries → "Outros"):
1 `#149cc6` · 2 `#c08428` · 3 `#8a6adf` · 4 `#cf5590` · 5 `#649a30`.

**Rampa sequencial** (magnitude — chuva, mapas de calor): `#9bd7ec → #57b7dc → #2c96c4 → #1d7cab → #166490 → #114e75`.

Todas as paletas foram validadas por contraste (≥3:1 sobre `#14181f`) e daltonismo. Regras: status nunca vira cor de série; nunca dois eixos y; texto usa tokens de texto, nunca a cor da série.

## Tipografia

- **Space Grotesk** 700/500 — números-síntese (48/34, tabular) e títulos de tela (24)
- **Inter** 600/500/400 — títulos de cartão (18), corpo (15), apoio (13)
- **JetBrains Mono** 500/400 — dados técnicos, timestamps, selos de fonte, ticker (12/11)

## Layout

Grid 12 colunas · conteúdo máx 1320px · gutter 24 · margens 24. Cartão: raio 14, padding 20, borda 1px, elevação por cor (sem sombra pesada). Spans: destaque 8 col · normal 4 · memória 6. Espaçamento em escala de 4 (4–48). Breakpoints 640/1024/1440.

## Componentes-chave e regras de produto

- **Selo de fonte** obrigatório em todo número/gráfico/mapa: "Fonte: X · há N min", com estado fresco (verde) / velho (âmbar) / fora (vermelho).
- **Badge de severidade**: pílula com círculo numerado + rótulo.
- **Cartão temático**: header (título + expandir ⤢) → número-síntese → apoio → micro-métricas/sparkline → selo. Expande em tela cheia com URL própria.
- **Ticker de leituras** (mono, rolagem contínua, ▲▼▬) e **feed "agora na cidade"** (timestamp + badge + linha) com toggle "só o anormal".
- **Seletor territorial global** no header ("Cidade inteira ▾") re-escopa a home; chips de filtro; botão "copiar link deste recorte" — todo filtro serializa na URL.
- **Fonte degradada**: banner âmbar honesto; nunca exibir dado velho como atual.
- Ciano só no que está vivo — se estiver em tudo, não destaca nada.
