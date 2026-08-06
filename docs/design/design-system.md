# riolive — design system (painel público de dados do Rio)

Painel web público, tema escuro, pt-BR. Conceito: **monitor de sinais vitais da cidade** — um **cockpit de viewport**: no desktop a home tem a altura exata da tela (zero rolagem de página), grade rígida de painéis com altura fixa por linha (nunca masonry, nunca buraco), conteúdo excedente rola dentro do próprio painel. Denso de dados ao vivo com hierarquia rígida; sóbrio; nunca estética militar (sem scanlines/HUD/verde-radar). No mobile vira pilha rolável. Nome e logo em definição: **não criar marca**; reservar espaço vazio ~140×28 no header.

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

## Tipografia (escala compacta de cockpit)

- **Space Grotesk** 700/500 — números-síntese (**28–32**, tabular; 44+ só no painel-destaque e no cabeçalho de estado), títulos de tela (16)
- **Inter** 600/500/400 — títulos de painel em CAPS (11), corpo (12), apoio (13)
- **JetBrains Mono** 500/400 — dados técnicos, timestamps, selos, ticker (10/11)

## Layout (modelo cockpit)

Largura total da tela (sem max-width) · margens 16 · gutter **12**. Grade 12 colunas × linhas de **altura fixa** (~280px em 1080p); painel preenche a célula inteira; alturas iguais por linha; buracos proibidos; excedente rola dentro do painel (fade na borda inferior). Painel: raio 10, padding 12–14, borda 1px, header fino em CAPS 11 com contador à direita. Espaçamento em escala de 4 (4–24). Breakpoints 640 (vira pilha rolável) / 1024 / 1440.

## Componentes-chave e regras de produto

- **Selo de fonte** obrigatório em todo número/gráfico/mapa: "Fonte: X · há N min", com estado fresco (verde) / velho (âmbar) / fora (vermelho).
- **Badge de severidade**: pílula com círculo numerado + rótulo.
- **Cartão temático**: header (título + expandir ⤢) → número-síntese → apoio → micro-métricas/sparkline → selo. Expande em tela cheia com URL própria.
- **Ticker de leituras** (mono, rolagem contínua, ▲▼▬) e **feed "agora na cidade"** (timestamp + badge + linha) com toggle "só o anormal".
- **Seletor territorial global** no header ("Cidade inteira ▾") re-escopa a home; chips de filtro; botão "copiar link deste recorte" — todo filtro serializa na URL.
- **Fonte degradada**: banner âmbar honesto; nunca exibir dado velho como atual.
- Ciano só no que está vivo — se estiver em tudo, não destaca nada.
