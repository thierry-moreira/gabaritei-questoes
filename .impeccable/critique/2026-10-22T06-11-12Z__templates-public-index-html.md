---
target: landing (templates/public/index.html)
total_score: 17
max_score: 28
na_heuristics: 7,9,10
p0_count: 0
p1_count: 2
target_identity: "file:C:\\Users\\Thierry\\Downloads\\Projetos Antigravity\\Projetos Antigravity\\gabaritei-questoes\\templates\\public\\index.html"
target_fingerprint: "sha256:8779c34f42eb4a0c2bcd36411f5387a9b27544b167f63836fd84fc1f36638f86"
target_path: "C:\\Users\\Thierry\\Downloads\\Projetos Antigravity\\Projetos Antigravity\\gabaritei-questoes\\templates\\public\\index.html"
timestamp: 2026-10-22T06-11-12Z
slug: templates-public-index-html
closed: true
---
DEGRADED: single-context (no sub-agent tool exposed). Target: templates/public/index.html (slug templates-public-index-html). Assessment A (design review) formed before Assessment B (detector, 28 findings).

## Design Health Score
Total: 17/28 (needs attention). n/a heuristics: 7, 9, 10 (persuade surface, static).
1 Visibility 3; 2 Match Real World 2 (MIT claim contradicted by "Todos os direitos reservados" footer); 3 Control 3; 4 Consistency 2 (landing accent #3b82f6 vs app Azul Aprovacao #2563eb; off-token eyebrow hexes); 5 Error Prevention 3; 6 Recognition 2 (CTA opens login wall, no visible signup path); 8 Aesthetic 2 (template skeleton: 5 eyebrows, 3-up icon cards, 4 identical green checklists).

## Design Specificity Verdict
Category-interchangeable edtech template. Single authored moment: tilted 3D floating browser mockup with real product screenshot (float 5s, pauses on hover). Real differentiator (MIT open source, local desktop, no paywall) is claimed in text but never proven: zero GitHub links; footer contradicts the claim. Detector caught what the review missed: primary CTA fails WCAG (white on gradient 3.7:1; sub-label #ebf3fe 0.75rem 3.3:1), badge 4.2:1, H1 accent span 3.2:1. 8 off-system colors, 2 off-scale radii (24px = frontmatter scale gap; prose documents it, YAML lacks xxl), 5 off-ramp sizes. False positives rejected: browser mockup dots, #1e293b-on-#0f172a static pairing. Accepted deliberately: Inter (documented app voice), directional mockup glow.

## Priority Issues
[P1] Primary CTA fails WCAG contrast (white 3.7:1, sub-label 3.3:1 on #3b82f6 gradient) — darken gradient to app blue (#2563eb) or solid Azul Aprovacao; sub-label >= 0.8rem. Suggested: /impeccable polish
[P1] Differentiator claimed but unproven + footer contradiction ("Todos os direitos reservados" vs MIT) — add GitHub link (nav + footer), MIT badge in final card, fix footer line. Suggested: /impeccable clarify
[P2] Template skeleton without own voice — kill 3-4 of 5 generic eyebrows, vary evidence format across showcases. Suggested: /impeccable bolder
[P2] Showcase dialect drift from DESIGN.md — align tokens or document the vitrine pair; add xxl 24px to rounded scale. Suggested: /impeccable colorize
[P3] Product mockup hidden on mobile (d-none d-lg-block) — static frame version for <lg. Suggested: /impeccable adapt

## Persona Red Flags
Jordan (First-Timer): "Começar Agora" opens login screen; no signup path visible on landing; nav lacks section anchors.
Riley (Stress Tester): fake address bar "painel.gabaritei.com.br"; "Todos os direitos reservados" vs MIT two sections above; global h2,h4 dark-color rule is a trap for dark surfaces.
Casey (Mobile): product screenshot entirely hidden on phones; otherwise light assets, big targets, no interruptions.

## What's Working
1. Tilted 3D mockup with real screenshot — authored trust moment; slow float, pauses on hover.
2. Honest claims discipline — post-paywall copy matches PRODUCT.md; no invented testimonials or numbers.
3. Single-scroll persuasive arc with working anchor and sticky nav.

## Minor Observations
Mockup address text 11px (decorative); will-change transform permanent on animated mockup; three labels for the same login destination; feature icon colors lack intent (blue/purple/default-blue mix); custom footer #0F172A hex loose.

## Questions to Consider
What if the real differentiator — open source, public code — were the hero instead of a footnote? What would this landing say if forbidden from eyebrow + 3 cards + checklist? Why does the only visual proof of the product vanish exactly on mobile?
