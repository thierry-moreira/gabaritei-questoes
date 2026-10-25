---
name: Gabaritei Questões
description: O Caderno Eye-Care — papel quente de dia, estúdio índigo à noite
colors:
  # Tema claro (eye-care, padrão do app)
  papel-eye-care: "#F7F5F0"
  cartao-claro: "#FFFFFF"
  cartao-elevado: "#FAF8F5"
  tinta-principal: "#262B27"
  tinta-secundaria: "#5F6661"
  linha-quente: "#E5E0D5"
  linha-suave: "#EFECE4"
  azul-serena: "#3D5A80"
  azul-serena-hover: "#324B6B"
  azul-realce: "#4B6B94"
  verde-estudo: "#2D6A4F"
  ambar-ofensiva: "#B45309"
  # Tema escuro ([data-bs-theme="dark"])
  estudio-noturno: "#08090D"
  sidebar-noturna: "#090B10"
  cartao-noturno: "#10131B"
  cartao-elevado-noturno: "#141822"
  tinta-noturna: "#E2E8F0"
  tinta-secundaria-noturna: "#94A3B8"
  indigo-noturno: "#5E6AD2"
  indigo-hover: "#6E79E0"
  indigo-claro: "#818CF8"
  verde-noturno: "#34D399"
  ambar-noturno: "#FBBF24"
  # Funcionais e dados
  vermelho-revisao: "#EF4444"
  branco: "#FFFFFF"
  grafico-claro: "#5A7BA6"
  grafico-noturno: "#38BDF8"
  # Gradientes
  gradiente-marca-claro: "linear-gradient(to top right, #3D5A80, #5A7BA6)"
  gradiente-marca-noturno: "linear-gradient(to top right, #4F46E5, #6366F1, #38BDF8)"
  gradiente-ofensiva-claro: "linear-gradient(145deg, #F0F6F2 0%, #E6EFE9 100%)"
  gradiente-ofensiva-noturno: "linear-gradient(145deg, #063428 0%, #032018 100%)"
typography:
  display:
    fontFamily: "Inter, sans-serif"
    fontSize: "1.875rem"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  streak:
    fontFamily: "Inter, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.02em"
  page-title:
    fontFamily: "Inter, sans-serif"
    fontSize: "clamp(1.5rem, 1.15rem + 1.1vw, 1.875rem)"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Inter, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Inter, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.6
  reading:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    letterSpacing: "0.04em"
  eyebrow:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.7rem"
    fontWeight: 800
    letterSpacing: "0.07em"
  caption:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 500
  icons:
    fontFamily: "bootstrap-icons-swap, Bootstrap Icons"
    fontSize: "1.15rem"
rounded:
  xs: "4px"
  sm: "6px"
  control: "8px"
  md: "10px"
  lg: "12px"
  alternative: "14px"
  card: "16px"
  premium: "20px"
  pill: "50px"
  round: "50%"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "28px"
  xxl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.azul-serena}"
    textColor: "#FFFFFF"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    height: "34px"
    padding: "0 16px"
  button-primary-hover:
    backgroundColor: "{colors.azul-serena-hover}"
    textColor: "#FFFFFF"
    rounded: "{rounded.control}"
  button-ghost:
    backgroundColor: "{colors.cartao-claro}"
    textColor: "{colors.tinta-principal}"
    rounded: "{rounded.control}"
    height: "34px"
    padding: "0 16px"
  header:
    height: "64px"
    backgroundColor: "rgba(247, 245, 240, 0.92)"
    blur: "12px"
  theme-icon-button:
    size: "32px"
    rounded: "{rounded.control}"
    backgroundColor: "{colors.cartao-claro}"
  metric-card:
    backgroundColor: "{colors.cartao-claro}"
    textColor: "{colors.tinta-principal}"
    rounded: "{rounded.card}"
    padding: "20px"
    minHeight: "148px"
  metric-icon:
    size: "40px"
    rounded: "{rounded.lg}"
    backgroundColor: "rgba(61, 90, 128, 0.1)"
  metric-label:
    textColor: "{colors.tinta-secundaria}"
    typography: "{typography.label}"
  chart-card:
    backgroundColor: "{colors.cartao-claro}"
    rounded: "{rounded.card}"
    padding: "24px"
  chart-range:
    backgroundColor: "{colors.cartao-elevado}"
    rounded: "{rounded.control}"
    padding: "4px"
  nav-item-active:
    backgroundColor: "rgba(61, 90, 128, 0.1)"
    textColor: "{colors.azul-serena}"
    rounded: "{rounded.lg}"
    padding: "0 14px"
  input-field:
    backgroundColor: "rgba(247, 245, 240, 0.5)"
    textColor: "{colors.tinta-principal}"
    rounded: "{rounded.lg}"
    padding: "10px 16px"
  form-label:
    textColor: "{colors.tinta-secundaria}"
    typography: "{typography.eyebrow}"
---

# Design System: Gabaritei Questões

## Overview

**Creative North Star: "O Caderno Eye-Care"**

O Gabaritei é uma estação de estudos feita para longas horas de leitura. O painel do aluno parte de uma folha de papel quente, quase sem brilho, onde a informação descansa sobre bordas finas e sombras discretas. A cor é recurso, não cenário: o azul sereno marca ação; o verde celebra progresso; o âmbar sinaliza ofensiva. O resultado é uma interface silenciosa no repouso e clara no momento de agir.

O **dual-theme é cidadão de primeira classe**. O tema claro `Papel Eye-Care` (`#F7F5F0`) e o tema escuro `Estúdio Noturno` (`#08090D`) não são inversões mecânicas: são duas casas desenhadas com a mesma hierarquia, os mesmos componentes e contrastes equivalentes. Toda cor de interface vive em variável CSS com par claro/escuro; o tema é escolhido pelo aluno e persiste no banco.

A tipografia é **Inter** em toda a área do aluno. **Outfit** aparece apenas na porta de entrada (login), e a landing pública mantém um dialeto visual próprio. Dentro do app, o dado é o herói: três métricas compactas, um gráfico de frequência e ações diretas.

**Key Characteristics:**
- Papel quente no claro; quase-preto com cartões azulados no escuro.
- Chrome compacto: rail lateral de 64px, header de 64px e conteúdo respirando em até 1600px.
- Azul sereno como voz de ação; índigo saturado reservado à noite e à visualização de dados.
- Superfícies de borda fina (1px), raio contido (8–16px) e sombra que só se revela na interação.
- Verde e âmbar com orçamento semântico: progresso e ofensiva, nunca decoração.
- Dados legíveis: 7/15/30 dias, escala Y dinâmica e tooltip com leitura direta.

## Colors

A paleta abandona o slate frio anterior. O tema claro é construído sobre neutros quentes de papel; o escuro, sobre um azul-preto profundo com cartões elevados em azul-acinzentado.

### Primary

- **Azul Serena** (`#3D5A80`; noite: `#5E6AD2`): a voz da ação. Botões primários do painel, link ativo da navegação, foco, seleção de texto e traço principal do gráfico. O hover claro escurece para `#324B6B`; no escuro clareia para `#6E79E0`.
- **Azul Realce** (`#4B6B94`; noite: `#818CF8`): o acento de apoio. Anel de progresso, fim do gradiente da linha do gráfico, ícones de destaque e anéis de foco translúcidos (10–14% de opacidade).

### Secondary / Semantic

- **Verde Estudo** (`#2D6A4F`; noite: `#34D399`): progresso real. Acertos, ofensiva ativa, badges de confirmação e o card de streak. No claro, o card usa o gradiente `#F0F6F2 → #E6EFE9`; no escuro, `#063428 → #032018`.
- **Âmbar Ofensiva** (`#B45309`; noite: `#FBBF24`): o pill de ofensiva no header e o badge "Aluno". É o único uso de âmbar no chrome.
- **Vermelho Revisão** (`#EF4444`): erro de alternativa, denúncia e ação destrutiva. Sempre em tinte translúcido no fundo (10%) e cor cheia no conteúdo.

### Neutral

- **Papel Eye-Care** (`#F7F5F0`) / **Estúdio Noturno** (`#08090D`): fundo principal do app.
- **Sidebar** (`#F7F5F0`; noite: `#090B10`): o rail mantém o mesmo papel do conteúdo no claro e um tom levemente mais escuro no escuro.
- **Cartão Claro** (`#FFFFFF`) / **Cartão Noturno** (`#10131B`): superfícies de conteúdo.
- **Cartão Elevado** (`#FAF8F5`; noite: `#141822`): controles segmentados, hovers e superfícies internas.
- **Tinta Principal** (`#262B27` / `#E2E8F0`) e **Tinta Secundária** (`#5F6661` / `#94A3B8`): texto e metadados.
- **Linha Quente** (`#E5E0D5`; noite: `rgba(255,255,255,0.07)`) e **Linha Suave** (`#EFECE4`; noite: `rgba(255,255,255,0.05)`): a costura de 1px entre superfícies.

### Data Visualization

- **Tema claro:** linha em gradiente `#5A7BA6 → #3D5A80 → #4B6B94`, área preenchida de azul-realce a 22% até transparente. Grid em tinta a 7%; eixo X em `#E2DDD3`.
- **Tema escuro:** linha em gradiente `#38BDF8 → #5E6AD2 → #818CF8`, área de índigo a 35% até transparente. Grid em branco a 5%; eixo X em branco a 6%.
- **Destaque do pico:** halo de 7,5px na cor de acento, ponto branco de 4,5px e borda de 2,5px. O rótulo do dia correspondente assume peso 600 e a cor de acento.
- **Tooltip:** superfície de cartão, borda de 1px, texto principal e padding de 12px; sem legenda e sem caixas de cor.

### Named Rules

**The Two Houses Rule.** Nenhuma cor de interface é escrita como literal em componente novo: toda cor vive em variável CSS com par claro/escuro. A exceção é a paleta do canvas do gráfico, declarada explicitamente em pares claro/escuro no JavaScript, porque o Chart.js não lê variáveis CSS diretamente. Se um hex aparece direto no CSS de componente, o tema quebra — é bug, não estilo.

**The Eye-Care Surface Rule.** No tema claro, superfícies grandes usam apenas neutros quentes de papel. Não introduza cinzas frios, brancos azulados ou slates como fundo de página: o conforto visual é parte da identidade.

**The Celebration Budget Rule.** Verde Estudo e Âmbar Ofensiva só aparecem onde há progresso real para celebrar (acertos, ofensivas, conquistas). Usá-los como decoração neutra dilui o significado.

## Typography

**Display Font:** Inter (fallback: sans-serif)
**Body Font:** Inter (fallback: sans-serif)
**Label Font:** Inter em caixa alta espaçada; KaTeX renderiza as fórmulas das questões.

**Character:** Uma única voz tipográfica, limpa e compacta, que prioriza horas de leitura de questões sobre personalidade de display. O tracking negativo fica reservado a títulos e números; labels ganham respiro em caixa alta. A exceção é Outfit na tela de login — a capa do caderno.

### Hierarchy

- **Números-herói** (700–800, 1.875–2.25rem, line-height 1–1.1): valor das métricas e da ofensiva. O número do streak é o maior elemento tipográfico do painel.
- **Page title** (700, `clamp(1.5rem, 1.15rem + 1.1vw, 1.875rem)`, tracking -0.02em): saudação do painel e títulos de página.
- **Headline** (700, 1.5rem, tracking -0.02em): títulos de seção e estados vazios.
- **Title** (600, 1rem, tracking -0.01em): título do gráfico e títulos de cartão.
- **Body** (400, 0.875rem, line-height 1.6): textos de apoio, subtítulos e metadados. A leitura de enunciados e alternativas sobe para 0.95rem.
- **Label** (500, 0.75rem, caixa alta, tracking +0.04em): rótulos das métricas.
- **Eyebrow** (800, 0.7rem, caixa alta, tracking +0.07em): labels de formulário e títulos de seção especiais.
- **Caption** (500, 0.6875–0.75rem): rodapés de cartão, hints e subtítulos do gráfico.
- **Chart ticks:** Y em monoespaçada de 10px; X em Inter 11px, com o pico em peso 600.

O piso de leitura é **11px** (`0.6875rem`). Micro-labels de chrome — a tag "Questões" e o badge "Aluno" — são as únicas exceções, entre 10px e 10.4px.

## Layout

O app é um **shell fixo de duas colunas**: rail lateral de **64px** à esquerda, header de **64px** e uma scroll-area interna — o corpo não rola no desktop, o conteúdo rola. O rail se expande para **260px** no hover, com transição de `0.28s cubic-bezier(0.4, 0, 0.2, 1)` e labels que aparecem ao expandir.

- **Sidebar:** ícones em botões de 40×40px, centralizados no rail; ao expandir, cada item vira uma linha com padding lateral de 14px. O item ativo usa tinte de Azul Serena a 10%, borda de 1px a 25% e raio de 12px — não é mais um bloco azul sólido.
- **Header:** 64px, fundo translúcido com `backdrop-filter: blur(12px)`, borda inferior de 1px. Contém marca compacta, pill de ofensiva, alternador de tema, divisor, avatar e menu do usuário.
- **Dashboard:** `max-width: 1600px`, centralizado; padding de `2rem 2.5rem` no desktop, `1.5rem 1.25rem` até 991px e `1.25rem 1rem` até 576px.
- **Boas-vindas:** título e subtítulo à esquerda, duas ações à direita; quebra em coluna no mobile. Margem inferior de 2rem.
- **Métricas:** grid Bootstrap de 3 colunas no desktop (`col-lg-4`), 2 no tablet (`col-md-6`) e 1 no mobile, com gutter de 1.25rem.
- **Gráfico:** cartão de largura total, com header próprio e corpo de 300px de altura; 230px no mobile.
- **Grid universal** (`.premium-grid`): `repeat(auto-fill, minmax(320px, 1fr))` com gap de 24px para as demais páginas de estudo.
- **Breakpoints:** 991px (tablet/padding), 768px (shell mobile/offcanvas), 576px (densidade) e 359px (ações do dashboard em coluna).

No mobile (≤768px) o shell colapsa: a sidebar vira um offcanvas Bootstrap ancorado à esquerda (`.mobile-sidebar`, fundo `--sidebar-bg`) e o body volta a rolar naturalmente.

## Elevation & Depth

**Camadas Silenciosas.** No repouso, a profundidade vem da costura: bordas de 1px separam superfície de fundo, e a sombra de cartão é quase imperceptível. A sombra acorda junto com a interação, mas sem exagero: os cards do dashboard não levitam, apenas confirmam o foco com borda e halo.

### Shadow Vocabulary

- **Cartão em repouso (claro):** `0 1px 3px rgba(38, 43, 39, 0.03), 0 4px 12px rgba(38, 43, 39, 0.02)`.
- **Cartão em repouso (escuro):** `0 1px 3px rgba(0, 0, 0, 0.2), 0 4px 12px rgba(0, 0, 0, 0.15)`.
- **Hover de cartão:** borda `--primary-border` + `--premium-shadow` (`0 1px 3px rgba(38,43,39,0.04), 0 8px 24px rgba(38,43,39,0.04)`; no escuro, `0 4px 20px rgba(0,0,0,0.35)`).
- **Botão do painel:** `0 1px 2px rgba(38,43,39,0.08)`; no hover, `translateY(-1px)` e nenhuma sombra pesada.
- **Flutuante:** `0 10px 40px rgba(0,0,0,0.15)`; no escuro, `rgba(0,0,0,0.4)` com blur de 12px.
- **Foco:** outline de 2px em Azul Serena com offset de 2px no painel; inputs usam anel de 4px em `--accent-soft` e borda de acento.

### Named Rules

**The Silent Layers Rule.** Superfícies repousam planas, com borda de 1px; sombra em repouso é quase nula por design. A única camada com sombra estrutural permanente é a flutuante (dropdown/modal). Se um card parado tem sombra visível, ele está gritando.

**The No-Lift Rule.** Cards de métrica e o cartão do gráfico não se deslocam no hover. O feedback é borda + sombra sutil. O lift de -6px continua restrito aos `.premium-card` de outras páginas.

## Shapes

A forma ficou mais contida que no sistema anterior: ações e controles usam **8px**, ícones e chips usam **10–12px**, cartões usam **16px** e o card premium legado mantém **20px**. A assinatura continua nos **pills de 50px/999px** do streak, dos badges e do avatar circular.

- **Header:** marca de 32×32px com raio 9px externo e 8px interno; botões de ícone de 32×32px com raio 8px; avatar de 32px circular.
- **Sidebar:** itens de 40×40px com raio 12px; labels em 0.875rem.
- **Dashboard:** botões de 34px de altura e raio 8px; controle de período com container de 8px e botões internos de 6px.
- **Métricas:** card de 16px; ícone de 40×40px com raio 12px; anel de progresso de 64px; watermark de fogo em 8rem.
- **Gráfico:** cartão de 16px; canvas sem moldura própria.
- **Alternativas:** container de 14px com borda de 1.5px; chip da letra de 32×32px e raio 10px.
- **Gradientes autorizados:** marca (azul serena no claro; índigo→azul no escuro), avatar, card de ofensiva, linha/área do gráfico, botão de IA e CTA público. Fora desses, cor é chapada.

## Components

### Shell Global

- **Header:** 64px, translúcido, com blur de 12px e borda inferior. A marca compacta usa um selo de 32px com gradiente e check; o nome "Gabaritei" leva a tag "Questões" em caixa alta (0.625rem, tracking 0.12em) em telas ≥576px.
- **Pill de ofensiva:** fundo âmbar a 10%, borda âmbar a 20%, raio 50px, padding 4px 10px, ícone de fogo e número em 0.75rem. No header, é o único âmbar.
- **Controles do header:** botão de tema de 32px com raio 8px; no escuro fica transparente e ganha fundo branco a 5% no hover. Avatar de 32px com gradiente `accent → primary` e anel de 2px em `primary-soft`.
- **Menu do usuário:** dropdown de 240px, raio 16px, padding 0.75rem, sombra flutuante; itens com raio 10px e hover em `primary-soft`.

### Navigation

- **Sidebar-rail:** 64px, ícones de 1.15rem; expande para 260px no hover.
- **Nav-link:** 40×40px no rail, raio 12px, peso 500; hover em `primary-soft` e ícone em escala 1.08. O item ativo usa tinte azul + borda de 1px + texto azul, sem sombra.
- **Mobile:** offcanvas de 280px, fundo `--sidebar-bg`, links com padding 14px 20px e sem transform no ativo.

### Dashboard

#### Boas-vindas e ações

- **Título:** `clamp(1.5rem, 1.15rem + 1.1vw, 1.875rem)`, peso 700.
- **Subtítulo:** 0.8125rem (0.875rem a partir de 768px), cor secundária. O percentual de evolução é sublinhado em Azul Serena e mostra "maior" ou "menor" conforme o sinal.
- **Ações:** `.btn-dash` com 34px de altura, raio 8px, padding 0 1rem, fonte 0.75rem/500 e gap de 0.5rem. A variante ghost usa cartão + borda; a primária usa Azul Serena e hover `--primary-hover`. No mobile, os botões dividem a largura; abaixo de 359px, empilham.

#### Metric Cards

- **Base:** `.metric-card`, fundo de cartão, borda de 1px, raio 16px, padding 1.25rem, altura mínima de 148px e sombra de repouso. No mobile, altura mínima de 132px, padding 1.1rem.
- **Contagem:** ícone de 40px em `primary-soft` com borda `primary-border` e raio 12px; badge verde translúcido à direita; label em caixa alta 0.75rem; valor 1.875rem/700.
- **Progresso:** anel SVG de 64px, stroke de 3.5px, trilha em `--ring-track` e preenchimento em Azul Realce; label e sublabel (0.875rem/600) ao lado; hint de 0.6875rem. O percentual aparece no centro do anel em 0.75rem/700.
- **Ofensiva:** variante com gradiente verde, borda verde, label 0.75rem/600 e valor 2.25rem/800; rodapé separado por borda de 1px. O ícone de fogo vira watermark de 8rem a 10% de opacidade. No escuro, gradiente verde profundo e texto claro.
- **Hover:** apenas borda `primary-border` e `--premium-shadow`; não há translate.

#### Frequência de Estudos

- **Cartão:** fundo de cartão, borda de 1px, raio 16px, padding 1.5rem (1.25rem no mobile) e sombra de repouso. O header tem borda inferior e padding-bottom de 1.5rem; o corpo começa com padding-top de 1.25rem.
- **Título/subtítulo:** 1rem/600 e 0.75rem em cor secundária.
- **Controle de período:** `.chart-range`, container inline-flex com fundo elevado, borda de 1px, raio 8px, padding 4px e gap de 2px. Cada botão tem raio 6px, fonte 0.75rem/500 e padding 0.3rem 0.75rem. O ativo usa fundo de cartão e sombra mínima no claro; no escuro, fundo branco a 10% e texto branco.
- **Opções:** 7, 15 e 30 dias, com `role="tablist"`, `aria-selected` e atualização dos dados sem recarregar a página.
- **Série:** linha de 3px, tensão 0.4, área em gradiente, pontos de 3.5px (4.5px no pico), hover de 6px e hit radius de 18px. O pico recebe halo e ponto branco.
- **Escala Y dinâmica:** `topo = max(4, ceil(pico / 4) * 4)` e `stepSize = topo / 4`, recalculados a cada troca de período. Não use mais a escala fixa de 24 com passo 6.
- **Tema:** o gráfico lê `data-bs-theme` e se atualiza via `MutationObserver` e evento `themeChanged`, sem recarregar.

### Buttons

- **Painel:** `.btn-dash` (34px, raio 8px, 0.75rem/500), com ghost e primário. Foco visível com outline de 2px e offset de 2px.
- **Legado:** `.btn-premium` mantém 12px de raio e padding 10px 24px; `.btn-premium-outline` fica em 38px de altura. O botão de IA continua em gradiente índigo→violeta com glow.
- **Mobile:** botões de ação usam 48px de altura em grade; a partir de 992px voltam à largura automática.

### Inputs / Fields

- **Style:** `.premium-input` e `.premium-select` com fundo translúcido (50% do body), borda de 1px, raio 12px, padding 0.65rem 1rem e peso 500.
- **Focus:** borda em Azul Realce + anel de 4px em `accent-soft`; fundo resolve para cartão.
- **Labels:** `.premium-label` em 0.7rem/800, caixa alta, tracking +0.07em, cor secundária.

### Alternatives (assinatura)

- **Container:** fundo de cartão, borda de 1.5px, raio 14px, padding 1rem 1.25rem e hover/selected em `primary-soft` com borda azul.
- **Chip da letra:** 32×32px, raio 10px, fundo neutro translúcido; quando marcado, preenche de Azul Serena com texto branco.
- **Estados:** correta = tinte verde 10% + borda e chip verdes; errada = idem em vermelho; eliminada = opacidade 0.3 + grayscale + texto riscado.

### Badges / Pills

- **Métrica:** badge pill de 0.6875rem/500, fundo verde 10%, borda verde 20% e texto verde.
- **Ofensiva:** pill de 50px em âmbar translúcido, usada no header.
- **Usuário:** badge "Aluno" em degradê âmbar, 0.65rem/800, caixa alta e tracking 0.05em.
- **Status gerais:** use os tons semânticos do sistema em `bg-*-subtle`; não invente uma terceira paleta para badges.

## Do's and Don'ts

### Do:

- **Do** escreva toda cor via variável CSS com o par claro/escuro mapeado (`var(--card-bg)`, `var(--primary-color)`, `var(--accent-color)`) — o tema é persistido por usuário.
- **Do** mantenha o claro sobre papel quente (`#F7F5F0`) e o escuro sobre `#08090D`; superfícies grandes não devem puxar para o cinza frio.
- **Do** preserve o chrome compacto: 64px de sidebar, 64px de header e cards de dashboard em 16px de raio.
- **Do** use Azul Serena para ação e Azul Realce para dados/foco; no escuro, o índigo assume o papel de ação.
- **Do** use Verde Estudo para acertos/streak e Vermelho Revisão para erros/destrutivo, sempre com tinte translúcido no fundo.
- **Do** mantenha as três opções de período (7/15/30) e a escala Y dinâmica (`max(4, ceil(pico / 4) * 4)`) ao mexer no gráfico.
- **Do** confira cada componente nos dois temas antes de fechar — contraste ilegível em qualquer tema é bug.

### Don't:

- **Don't** reintroduza a paleta antiga (`#2563eb`, `#1e40af`, `#f1f5f9`, `#0d1117`, `#161b22`) nem os nomes "Papel de Estudos"/"Grafite da Madrugada".
- **Don't** hardcode hex em CSS de componente — quebra o dual-theme. Exceções legadas devem ser migradas para tokens quando tocadas; a paleta do canvas é declarada no JS em pares claro/escuro.
- **Don't** adicione sombra visível ou lift a superfícies em repouso; o dashboard usa borda + sombra sutil, sem translate.
- **Don't** introduza fontes novas no app (Inter é a voz; Outfit só no login) nem gradientes fora dos autorizados.
- **Don't** use Âmbar Ofensiva ou Verde Estudo como decoração sem progresso real — é o Orçamento de Celebração.
- **Don't** crie texto de leitura abaixo de 11px; micro-labels de chrome (tag da marca e badge "Aluno") são a única exceção.
- **Don't** troque a escala do gráfico por um valor fixo: ela precisa acompanhar o pico do período selecionado.

## Implementation Map

| Área | Arquivo |
| --- | --- |
| Rota e dados do painel (`/aluno/painel`) | `rotas/aluno.py` |
| Template do dashboard | `templates/aluno/dashboard.html` |
| Macro dos metric cards | `templates/components/stat_card.html` |
| Shell, header, sidebar e tokens | `templates/base_aluno.html`, `static/css/base_aluno_layout.css` |
| Componentes compartilhados | `static/css/components.css`, `static/css/shared_premium.css` |
| Estilos exclusivos do painel | `static/css/dashboard_minimal.css` |

O dashboard monta três métricas (questões resolvidas, taxa de acerto e ofensiva), o gráfico de frequência com 7/15/30 dias e as ações "Raio-X Completo" e "Resolver Questões". A evolução semanal usa o sinal do percentual para escolher entre "maior" e "menor". O CSS do painel não redefine os tokens-base; a paleta do Chart.js é declarada em pares claro/escuro dentro do template do dashboard, porque o canvas não consome variáveis CSS diretamente.
