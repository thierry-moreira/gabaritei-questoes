# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

O usuário primário é o **aluno concurseiro brasileiro**: estuda para concursos públicos em sessões longas de estudo, na própria máquina, e precisa que o progresso (questões resolvidas, simulados, revisões de flashcards, cadernos, resumos) sobreviva entre máquinas. O app é o "app do aluno" de um ecossistema de dois repositórios — o painel administrativo (gestão de questões e taxonomia) vive em repo privado separado (`gabaritei-admin`) e não faz parte deste escopo. *(inferido do repositório; ajuste se o público-alvo for outro)*

## Product Purpose

O Gabaritei Questões acelera a aprovação em concursos públicos. Ele dá ao aluno: banco de questões reais com gabarito comentado e discussões; simulados completos com pontuação, ranking e PDF; flashcards com repetição espaçada (SRS) e revisões do dia; resumos por matéria gerados por IA; cadernos de questões personalizados; análise estruturada de editais; e estatísticas de desempenho. Sucesso = o aluno mantém uma rotina de estudo constante (ofensiva/streak diário, revisões em dia) e gabarita a prova alvo.

## Positioning

Plataforma de estudos **desktop local, software livre (MIT), com IA** — modelo confirmado pelo dono. O app roda na máquina do aluno (Electron como casca + Flask local em `127.0.0.1:5000`, 100% offline-first no front), enquanto o progresso fica na nuvem vinculado à conta real (Supabase Auth) — o aluno continua de onde parou em qualquer máquina. Vizinhos SaaS não copiam honestamente: código aberto e gratuito, sem muros de paywall (todo usuário autenticado tem acesso completo), e segurança que vive no banco (policies RLS), não na confiança no cliente.

## Operating Context

- Sessões de estudo longas em desktop Windows: o shell Electron spawna o backend Flask e abre uma janela limpa de app (menu oculto); links externos abrem no navegador do sistema.
- Conta real com e-mail e senha (Supabase Auth); a sessão é lembrada entre execuções via refresh token persistido na sessão Flask.
- Dados no Supabase (PostgreSQL) via chave ANON **pública por design**: leitura de conteúdo liberada; escrita dos dados do aluno exige o header `x-app-token` **e** a identidade do dono (`auth.uid()` amarrado a `usuarios.auth_id`). A `service_role` jamais embarca no app.
- Execução local em HTTP puro: HTTPS/HSTS/cookie Secure desativados por design (Talisman); escuta apenas em `127.0.0.1`.
- Desenvolvimento: `python app.py` (http://127.0.0.1:5000); shell via `cd desktop; npm start`; testes 100% isolados (`rodar_testes.bat`).

## Capabilities and Constraints

Funcionalidades confirmadas (11 blueprints em `rotas/`):

- **auth** — cadastro, login, recuperação de senha e logout (Supabase Auth)
- **aluno** — dashboard principal e área de estudos (ofensiva/streak, flashcards do dia)
- **questoes** — resolver, visualizar (lista e individual), gabaritos comentados, discussões
- **caderno** — cadernos de questões agrupadas sob medida pelo estudante
- **filtro** — filtros complexos de disciplinas, bancas e anos
- **simulado** — criação, resposta, pontuação, ranking, resultado e PDF
- **edital** — exibição e análise estruturada de editais de concursos
- **flashcards** — SRS: repetição espaçada, revisões do dia, status dos cartões
- **resumos** — cadernos de resumos por matéria, com geração automática via IA (OpenAI) e exclusão individual ou total
- **conta** — perfil, preferências, reset dos dados de estudo, exclusão da conta
- **api** — endpoints assíncronos internos do frontend

Restrições técnicas confirmadas:

- Flask (Python) + templates Jinja2 + Bootstrap 5.3 + Bootstrap Icons + fonte Inter; CSS customizado por área em `static/css/`; JS por área em `static/js/`
- Shell Electron (`desktop/main.js`) com zero código de produto; build PyInstaller/NSIS planejado em fases
- CSP rigorosa via Talisman; gzip automático; rate limiting global; logging estruturado
- Licença MIT (`LICENSE`) — nota: `package.json` ainda declara ISC (divergência menor a corrigir)

**Fato confirmado de produto:** o modelo é **software livre total** — todo aluno autenticado tem acesso completo, sem paywall, trial ou planos. O legado freemium foi removido do código e da copy: a landing de apresentação foi aposentada (a raiz `/` abre direto o login), as páginas públicas de questões funcionam como vitrine (visitante lê, mas só aluno cadastrado responde — o card mostra "Cadastre-se para responder"), e a flag `is_premium` não existe mais no código. Trabalhos futuros não podem reintroduzir planos, preços, trials ou muros que o produto não tem.

## Brand Commitments

- Nome: **Gabaritei** (Gabaritei Questões)
- Tagline: "Domine as questões, conquiste a vaga."
- Assets de marca existentes: `static/logo.webp` (logo) e `static/icone.webp` (ícone/favicon)
- Voz: português do Brasil, motivacional e focada em aprovação
- Compromissos públicos: software livre MIT; modelo de segurança documentado abertamente (`docs/banco_dados.md`); app do aluno sem nenhum código administrativo

## Evidence on Hand

- Screenshots reais do produto em `static/imagens/index/`: `painel_aluno_fiel.webp`, `flashcards.webp` e capturas de tela do fluxo de index (2026-04-30)
- Landing de apresentação removida (out/2026): a raiz `/` abre direto a tela de login; o link "Código-fonte" (GitHub) migrou para o rodapé do login. Screenshots históricos da ex-landing permanecem em `static/imagens/index/`
- Documentação técnica completa: `README.md`, `docs/app.md`, `docs/desktop.md`, `docs/banco_dados.md`, `docs/rotas/*.md`
- **Ausências que futuros trabalhos não devem fabricar:** não há depoimentos de alunos, taxas de aprovação comprovadas, números de usuários, estudos de caso, matérias de imprensa ou prêmios. Nenhuma superfície pode inventar essas provas.

## Product Principles

1. **Local-first, progresso na nuvem** — o app vive na máquina do aluno; a conta na nuvem garante continuidade entre máquinas, não dependência de servidor próprio.
2. **Segurança no banco, não no cliente** — a chave ANON é pública por design; toda proteção vive em policies RLS, token de escrita e identidade do dono.
3. **Liberdade total ao aluno autenticado** — sem paywall, sem limites artificiais: todo usuário tem acesso completo ao produto.
4. **Ferramentas de estudo de verdade, não vitrine** — questões, SRS, simulados e estatísticas fazem o trabalho pesado; a IA serve o estudo (resumos), não substitui o aluno.
5. **Transparência de engenharia** — código aberto, docs públicos do modelo de segurança, licença aberta.
