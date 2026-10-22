---
name: Gabaritei Questões
description: O Caderno Premium — estação de estudos dual-theme para concurseiros, elegante e celebratória
colors:
  # Tema claro (padrão do app)
  azul-aprovacao: "#2563eb"
  azul-aprovacao-escuro: "#1e40af"
  azul-suave: "#eff6ff"
  indigo-foco: "#6366f1"
  papel-de-estudos: "#f1f5f9"
  cartao-claro: "#ffffff"
  tinta-principal: "#1e293b"
  tinta-secundaria: "#475569"
  linha-clara: "#e2e8f0"
  # Tema escuro ([data-bs-theme="dark"])
  azul-aprovacao-noturno: "#58a6ff"
  indigo-foco-noturno: "#818cf8"
  grafite-da-madrugada: "#0d1117"
  cartao-noturno: "#161b22"
  tinta-principal-noturna: "#e6edf3"
  tinta-secundaria-noturna: "#8b949e"
  linha-escura: "#30363d"
  # Funcionais (ambos os temas)
  verde-gabarito: "#10b981"
  vermelho-revisao: "#ef4444"
  dourado-streak: "#f59e0b"
  # Acentos das superfícies públicas (login/landing)
  roxo-vitrine: "#7c3aed"
typography:
  display:
    fontFamily: "Inter, sans-serif"
    fontSize: "2.8rem"
    fontWeight: 800
    lineHeight: 1
  headline:
    fontFamily: "Inter, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Inter, sans-serif"
    fontSize: "1.1rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.7rem"
    fontWeight: 800
    letterSpacing: "0.07em"
  icons:
    fontFamily: "bootstrap-icons-swap, Bootstrap Icons"
    fontSize: "1.15rem"
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  xxl: "24px"
  pill: "50px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "28px"
components:
  button-primary:
    backgroundColor: "{colors.azul-aprovacao}"
    textColor: "#ffffff"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "10px 24px"
  button-primary-hover:
    backgroundColor: "{colors.azul-aprovacao-escuro}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
  button-ia:
    backgroundColor: "{colors.indigo-foco}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "0 18px"
    height: "38px"
  card-study:
    backgroundColor: "{colors.cartao-claro}"
    textColor: "{colors.tinta-principal}"
    rounded: "{rounded.lg}"
    padding: "24px"
  stat-card:
    backgroundColor: "{colors.cartao-claro}"
    textColor: "{colors.tinta-principal}"
    rounded: "{rounded.xl}"
    padding: "28px"
  nav-item-active:
    backgroundColor: "{colors.azul-aprovacao}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "12px 20px"
  input-field:
    backgroundColor: "{colors.cartao-claro}"
    textColor: "{colors.tinta-principal}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  form-label:
    textColor: "{colors.tinta-secundaria}"
    typography: "{typography.label}"
---

# Design System: Gabaritei Questões

## Overview

**Creative North Star: "O Caderno Premium"**

O Gabaritei é uma estação de estudos elegante e acolhedora que celebra o progresso do aluno. A interface vive de silêncio e de recompensa: superfícies repousam sobre bordas finas de 1px e sombras quase imperceptíveis, reservando cor e movimento para os momentos que importam — um acerto marcado em Verde Gabarito, a ofensiva de estudos em degradê esmeralda, o cartão que levita suavemente quando o cursor o visita. Nada decora por decoração; cada acento aponta para progresso real de estudo.

A identidade profunda do sistema é o **dual-theme como cidadão de primeira classe**. O modo escuro (Grafite da Madrugada, `#0d1117`) não é uma inversão da folha de estudos — é uma segunda casa tão cuidada quanto o tema claro (Papel de Estudos, `#f1f5f9`), pensada para as sessões noturnas longas do concurseiro. Toda cor vive em par claro/escuro por meio de variáveis CSS; o tema é do aluno e persiste no banco. A tipografia é Inter em toda a área do aluno; Outfit aparece apenas na porta de entrada (login), e a landing pública usa Inter com gradiente Azul→Roxo de vitrine.

**Key Characteristics:**
- Silêncio visual no repouso; celebração pontual no progresso (verde, esmeralda, dourado)
- Tema duplo real: cada token existe em par claro/escuro, sem hex hardcoded
- Superfícies de borda fina (1px) com profundidade que só acorda no hover
- Inter como voz única do app; raio generoso (12–20px) e pills de 50px
- Shell de app fixo (sidebar-rail + scroll-area), denso mas respirável

## Colors

A paleta é uma folha de estudos em tons de slate, pontuada por dois acentos de foco e três cores de significado — e cada tonalidade tem seu par noturno.

### Primary
- **Azul Aprovação** (#2563eb; noite: #58a6ff): a voz da ação. Botões primários, link ativo da navegação, foco dos formulários e o micro-lift de interação. No escuro clareia para manter o mesmo peso percebido.
- **Azul Aprovado Escuro** (#1e40af): o estado hover do botão primário no tema claro.

### Secondary
- **Índigo Foco** (#6366f1; noite: #818cf8): o acento de contraste para recursos de destaque (IA, destaques, anéis de progresso) e o focus-ring translúcido (10–15% de opacidade) de inputs e hovers.
- **Roxo Vitrine** (#7c3aed): o par do botão IA — fecha o degradê 135° dos CTAs públicos (login/landing), que abre em Azul Aprovação (#2563eb): conversão ancorada nos tokens do app, sem dialeto divergente.

### Tertiary
- **Verde Gabarito** (#10b981): celebração — acerto da alternativa, ofensiva (streak em degradê esmeralda #059669→#064e3b no escuro, #6ee7b7→#34d399 no claro), confirmações.
- **Vermelho Revisão** (#ef4444): erro da alternativa e ações destrutivas, sempre como tinte translúcido (10%) no fundo e cor cheia no conteúdo.
- **Dourado Streak** (#f59e0b→#d97706 em degradê): o badge "Aluno" no menu do usuário — único uso de âmbar no sistema.

### Neutral
- **Papel de Estudos** (#f1f5f9) / **Grafite da Madrugada** (#0d1117): fundos principais claro/escuro.
- **Cartão Claro** (#ffffff) / **Cartão Noturno** (#161b22): superfícies de conteúdo.
- **Tinta Principal** (#1e293b / #e6edf3) e **Tinta Secundária** (#475569 / #8b949e): texto e metadados.
- **Linha Clara** (#e2e8f0) / **Linha Escura** (#30363d): a costura de 1px que separa superfícies.

### Named Rules
**The Two Houses Rule.** Nenhuma cor é escrita como literal em componente: toda cor vive em variável CSS com par claro/escuro (`var(--primary-color)` ↔ valor noturno em `[data-bs-theme="dark"]`). Se um hex aparece direto no CSS de componente, o tema quebra — é bug, não estilo.
**The Celebration Budget Rule.** Verde Gabarito e Dourado Streak só aparecem onde há progresso real para celebrar (acertos, ofensivas, conquistas). Usá-los como decoração neutra dilui o significado.

## Typography

**Display Font:** Inter (fallback: sans-serif)
**Body Font:** Inter (fallback: sans-serif)
**Label/Mono Font:** Inter em caixa alta espaçada para labels; KaTeX renderiza as fórmulas das questões.

**Character:** Uma única voz tipográfica, limpa e levemente condensada no negrito (tracking -0.02em), que prioriza horas de leitura de questões sobre personalidade de display. A exceção é Outfit na tela de login — a capa do caderno.

### Hierarchy
- **Display** (800, 2.8rem, line-height 1): o número-herói do dashboard (taxa de acerto, questões resolvidas); no mobile encolhe para 2rem.
- **Headline** (700, 1.5rem, tracking -0.02em): títulos de página e de seção; a landing usa display maior (800, tracking -0.04em) para o hero.
- **Title** (600, 1.1rem, tracking -0.02em): títulos de cartão e dropdown-headers.
- **Body** (400–500, 0.95rem, line-height 1.6): enunciados, alternativas e texto corrido — a medida de leitura da questão é o coração do produto.
- **Label** (800, 0.7rem, tracking +0.07em, caixa alta): rótulos de formulário e eyebrows; badges usam 700 a 0.65–0.85rem.

## Layout

O app é um **shell fixo de duas colunas**: sidebar-rail de 70px à esquerda que se expande para 260px no hover (ícones + labels com transição 0.3s), header de 74px (64px no mobile) e scroll-area interna — o corpo não rola, o conteúdo rola. No mobile (≤768px) o shell colapsa: a sidebar vira offcanvas Bootstrap ancorada à esquerda (classe `.mobile-sidebar`, fundo `--sidebar-bg`, nav-links sem transform ativo) e o body volta a rolar naturalmente.

- **Grid de cartões universal** (`.premium-grid`): `repeat(auto-fill, minmax(320px, 1fr))` com gap de 24px — o dashboard, resumos e editais respiram igual.
- **Containers de conteúdo**: centrados com `max-width` moderado (850px na conta, 1140px Bootstrap nos fluxos de estudo); a questão individual usa col-lg-10.
- **Breakpoints**: 768px (mobile/offcanvas) e 576px (densidade: cartões caem para raio 12px, padding 1.25rem, estatísticas 2rem).
- **A landing pública** é dialeto separado: fluxo único vertical, hero com mockup inclinado, seções Bootstrap de largura controlada, sem shell de app.

## Elevation & Depth

**Camadas Silenciosas.** No repouso, a profundidade vem da costura: bordas de 1px (Linha Clara/Escura) separam superfície de fundo, e a sombra ambiente é deliberadamente invisível — `0 4px 20px rgba(0,0,0,0.03)` no claro, `rgba(0,0,0,0.2)` no escuro. A sombra acorda junto com a interação: ao hover, o cartão levita (-2 a -6px) e ganha uma sombra real (`0 20px 40px -10px` no claro, `-12px rgba(0,0,0,0.5)` no escuro). Overlays flutuantes (dropdowns, modais) são a única camada com sombra estrutural permanente (`0 10px 40px rgba(0,0,0,0.15)`; no escuro, + backdrop-blur de 10–12px).

### Shadow Vocabulary
- **Ambiente** (`0 4px 20px rgba(0,0,0,0.03)` / dark `0.2`): repouso de cartões e o `.shadow-sm` global.
- **Funcional de botão** (`0 4px 6px -1px rgba(0,0,0,0.1)`; hover `0 10px 15px -3px 0.2`): a única sombra de repouso não-superfície — ancoragem mínima do botão primário.
- **Lift de hover** (`0 20px 40px -10px rgba(0,0,0,0.12)`; dark `-12px 0.5`): cartões premium e stats ao hover.
- **Flutuante** (`0 10px 40px rgba(0,0,0,0.15)`; dark `0.4` + blur): dropdowns e modais.
- **Glow de foco** (`box-shadow: 0 0 0 4px` em Índigo Foco a 10–15%): inputs e estados ativos — anel, nunca halo.

### Named Rules
**The Silent Layers Rule.** Superfícies repousam planas com borda de 1px; sombra em repouso é quase nula por design. As duas exceções autorizadas: a ancoragem funcional mínima do botão primário e a camada estrutural de elementos flutuantes (dropdown/modal). Se um card parado tem sombra visível, ele está gritando.

## Shapes

Forma macia e consistente: cartões arredondam generosamente (raio 16px no base, 20px nos premium/stats, 24px em empty-states e conta), controles intermediários usam 12px (botões, nav, inputs, botões-icon, ícones de estatística) e o legado de 8px sobrevive em elementos pontuais. A assinatura de forma são os **pills de 50px**: ofensiva no header, labels de desempenho, badge do usuário, e CTAs públicos frequentes em `rounded-pill`. Chips de letra das alternativas usam 10px. O empty-state usa borda tracejada de 2px — o único traço não-sólido do sistema — e a capa de vidro do login arredonda ainda mais (raio 2.5rem = 40px), a superfície mais suave do produto. Gradientes 135° aparecem em quatro lugares apenas: card de ofensiva (esmeralda), header de modal (índigo profundo #4f46e5→#3730a3), botão de IA (índigo→violeta #4f46e5→#7c3aed) e CTA público (Azul→Roxo Vitrine).

## Components

### Buttons
- **Shape:** raio 12px; padding 10px 24px; peso 600; ícone+texto com gap de 8px.
- **Primário:** Azul Aprovação sólido, texto branco, ancoragem funcional `0 4px 6px -1px` a 10%; hover escurece para #1e40af, levita -2px e a sombra cresce (`0 10px 15px -3px` a 20%); active `translateY(0) scale(0.98)`. No mobile encolhe para `8px 12px`/0.8rem.
- **IA:** variante `.btn-ai-premium` — degradê 135° índigo→violeta (#4f46e5→#7c3aed), altura 38px, glow índigo `0 4px 12px` a 30%: a porta para os recursos de Gabi IA.
- **Ghost variants:** `outline` (borda 1.5px Linha, altura 38px; hover tinge azul-suave, borda azul e levita -1px), `success` (Verde Gabarito translúcido no hover) e `danger` (Vermelho Revisão idem) — fundo transparente no repouso.
- **CTA público (login/landing):** degradê 135° Azul→Roxo Vitrine, altura 3.75rem, raio 16px, glow azul 0.3 — a única sombra colorida fora do botão de IA.

### Cards / Containers
- **Cartão base:** fundo Cartão, borda 1px Linha, raio 16px, transição de tema 0.3s.
- **Premium card:** raio 20px, padding 24px; hover levita -6px, borda vira Índigo Foco e acende o Lift de hover.
- **Stat card:** raio 20px, padding 28px, valor Display 2.8rem/800; hover -5px + tinte azul-suave; a variante streak é degradê esmeralda com texto branco e marca-d'água de fogo 🔥 a 20% de opacidade. Derivados: **badge-today** (pill esmeralda translúcido no canto superior do cartão de hoje) e **anel de progresso** (`circular-progress-mini`, 70px, conic-gradient com `--progress-percent`, texto 800 no centro).
- **Empty state:** raio 24px, borda tracejada 2px, padding 4rem 2rem.

### Inputs / Fields
- **Style:** fundo translúcido (50% do body-bg), borda 1px Linha, raio 12px, padding 0.65rem 1rem, peso 500.
- **Focus:** borda Índigo Foco + anel de 4px a 10–15%; fundo resolve para Cartão.
- **Labels:** premium-label — 0.7rem, 800, caixa alta, +0.07em, Tinta Secundária.

### Navigation
- **Sidebar-rail:** 70px, ícones 1.15rem; expande a 260px no hover com labels em fade.
- **Nav-link:** raio 12px, peso 500; hover tinge azul-suave e desliza +4px; **ativo** vira pill Azul Aprovação com texto branco e glow `0 4px 12px` azul-suave.
- **Dropdown:** menu raio 16px, padding 0.75rem, itens raio 10px com hover que desliza +4px e escala o ícone.

### Question Alternatives (assinatura)
- **Container:** raio 10px via chip de letra quadrado-arredondado, borda 1px, fundo branco/noite Cartão; letra em chip (10px) que preenche de Azul Aprovação quando marcada.
- **Estados:** correta = tinte Verde Gabarito 10% + borda verde + chip verde; errada = idem em Vermelho Revisão; eliminada (tesoura) = opacidade 0.3 + grayscale + texto riscado.

### Badges / Pills
- Pills de 50px para ofensiva (streak), desempenho e badge "Aluno" (degradê dourado); badges Bootstrap semânticos para matéria/dificuldade usam os tons do sistema (bg-*-subtle).

## Do's and Don'ts

### Do:
- **Do** escreva toda cor via variável CSS com o par claro/escuro mapeado (`var(--card-bg)`, `var(--primary-color)`) — o tema é persistido por usuário.
- **Do** mantenha a borda de 1px como separador padrão de superfícies; profundidade acorda no hover.
- **Do** use Verde Gabarito para acertos/streaks e Vermelho Revisão para erros/destrutivo, sempre com tinte translúcido no fundo.
- **Do** confira cada componente nos dois temas antes de fechar — contraste ilegível em qualquer tema é bug.
- **Do** mantenha Inter na área do aluno e o degradê 135° restrito aos quatro lugares autorizados (streak, modal-header, botão IA, CTA público).

### Don't:
- **Don't** hardcode hex em CSS de componente — quebra o dual-theme (a skill `design-system` do repo já proíbe; o DESIGN.md herda).
- **Don't** adicione sombra visível a superfícies em repouso — o sistema é Camadas Silenciosas.
- **Don't** introduza fontes novas no app (Inter é a voz; Outfit só no login) nem gradientes fora dos autorizados.
- **Don't** use Dourado Streak ou Verde Gabarito como decoração sem progresso real — é o Orçamento de Celebração.
- **Don't** crie texto funcional abaixo de 11px (o mínimo observado é o label 0.7rem ≈ 11.2px).


