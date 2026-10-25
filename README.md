<div align="center">
  <img src="static/icone.webp" width="104" alt="Gabaritei Questões" />

# Gabaritei Questões

**Domine as questões, conquiste a vaga.**

Plataforma de estudos para concursos com inteligência artificial — **questões comentadas, simulados, flashcards, resumos, cadernos e editais**. Software livre e sem paywall: todo aluno cadastrado usa tudo, e o progresso fica na nuvem com a própria conta.

[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg)](./LICENSE)
![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-backend-000000?logo=flask&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Postgres%20%2B%20RLS-3ECF8E?logo=supabase&logoColor=white)
![Electron](https://img.shields.io/badge/Electron-shell-47848F?logo=electron&logoColor=white)

[Recursos](#recursos) · [Arquitetura](#arquitetura) · [Segurança](#modelo-de-seguranca) · [Instalação](#instalacao) · [Testes](#testes) · [Documentação](#documentacao)

<img src="static/imagens/index/painel_aluno_fiel.webp" alt="Painel do aluno — estatísticas, taxa de acerto e ofensiva" width="840" />
</div>

---

<a id="recursos"></a>
## ✨ Recursos

| | |
|---|---|
| 📝 **Questões comentadas** | Explicação pedagógica gerada por IA para cada questão, além de comentários da comunidade com moderação automática |
| 📋 **Simulados** | Monte simulados personalizados e acompanhe o desempenho por matéria |
| 🧠 **Flashcards** | Revisão com repetição espaçada (SM-2 customizado), sessão com flip, avaliação 0–3 e estados vazio/final |
| 🤖 **IA de estudos (BYOK)** | Explicações, resumos e flashcards gerados pela **sua própria chave de API** (OpenAI, Google Gemini ou Anthropic), configurada em Configurações da conta e guardada só no seu dispositivo (cifrada com DPAPI) — explicações geradas ficam salvas no banco (cache global para todos os alunos) |
| 📑 **Editais** | Trilha de estudo por edital, com progresso por tópico e ciclo de revisão |
| 📚 **Cadernos e filtros** | Coleções de questões salvas e filtros de busca reutilizáveis |
| 📊 **Painel do aluno** | Estatísticas, curva de esquecimento, meta diária e ofensiva (streak calculado no horário de Brasília) |
| ☁️ **Conta na nuvem** | Login com e-mail e senha (Supabase Auth) — o progresso acompanha o aluno em qualquer máquina, com sessão lembrada entre execuções |
| 🌗 **Tema claro/escuro** | Preferência salva na conta |

<a id="arquitetura"></a>
## 🧱 Arquitetura

```text
Electron (janela do app)  ──spawna──▶  Flask (127.0.0.1:5000)  ──HTTPS──▶  Supabase (PostgreSQL)
     desktop/main.js                        app.py + rotas/                   PostgREST + Auth + RLS
```

| Camada | O quê | Onde |
|---|---|---|
| **Shell** | Janela do app — spawna o backend e abre direto na tela de login | `desktop/main.js` |
| **Backend** | Flask com **11 blueprints** (aluno, questões, simulados, flashcards, editais, cadernos, IA, auth…) | `app.py`, `rotas/` |
| **Banco** | Supabase (PostgreSQL) acessado via **chave ANON pública** — toda a segurança vive em policies RLS no banco | `docs/banco_dados.md` |
| **Página de e-mail** | Página estática no GitHub Pages que recebe o redirect dos e-mails do Auth (confirmação de cadastro e redefinição de senha) | `site/` |

<a id="modelo-de-seguranca"></a>
## 🔐 Modelo de segurança

- **Conteúdo é aberto, dados do aluno são do dono**: questões, matérias e taxonomia são legíveis por qualquer visitante; já o histórico, flashcards, resumos, simulados e editais do aluno só são lidos e escritos pelo próprio dono (RLS por `auth.uid()` vinculado a `usuarios.auth_id`).
- **Escrita exige dois fatores**: o header `x-app-token` (segredo de app, migration `rls_header_app_aluno`) **e** a identidade do dono no JWT — mesmo que alguém extraia a ANON key **e** o token do binário, não consegue tocar dados de outro aluno.
- **A chave `service_role` nunca** faz parte deste app: a gestão de conteúdo roda num painel separado, com 2FA próprio.
- **Perfis legados são adotados no 1º login**: alunos do sistema antigo (passwordless) têm o perfil re-vinculado à conta Auth pelo próprio RLS, sem duplicação.
- Detalhes completos: [docs/banco_dados.md](docs/banco_dados.md)

<a id="instalacao"></a>
## 🛠️ Instalação (dev)

**Pré-requisitos:** Python 3.12+, Node.js (apenas para o shell Electron) e um projeto Supabase. Os recursos de IA usam a chave do próprio aluno (BYOK — OpenAI, Google Gemini ou Anthropic, configurada pela UI da conta).

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env                       # preencha SUPABASE_URL, ANON key, APP_TOKEN e FLASK_SECRET_KEY
copy desktop\token.example.js desktop\token.local.js   # o MESMO APP_TOKEN do .env
python app.py                                # http://127.0.0.1:5000
```

Shell Electron (dev):

```powershell
cd desktop
npm install
npm start          # spawna o Flask do venv e abre a janela
```

Gerar o executável do Windows (backend PyInstaller + runtime GTK + instalador NSIS):

```powershell
powershell -ExecutionPolicy Bypass -File desktop\build.ps1
# → desktop\dist\GabariteiAluno-Setup-x.y.z.exe (+ win-unpacked portátil)
```

> O PDF de simulados funciona **out-of-the-box**: o instalador embarca o runtime GTK (Pango/FontConfig, LGPL) junto ao backend — nada é instalado no sistema do usuário.

> A ANON key é **pública por design** (vai embarcada no binário) — a segurança do produto vive nas policies RLS, não no segredo da chave. O `service_role` nunca é usado aqui. Detalhes completos do build: [docs/desktop.md](docs/desktop.md).

<a id="testes"></a>
## ✅ Testes

```powershell
.\rodar_testes.bat          # ou: python -m unittest discover -s tests
```

Suíte 100% isolada (sem rede, sem banco real) cobrindo login e cadastro, re-link de perfis legados, questões e streaks, simulados, flashcards (incluindo rota global, estado vazio e validações da revisão), editais, IA, cadernos, resumos e honeypots de segurança. Especificação completa em [tests/README.md](tests/README.md).

<a id="documentacao"></a>
## 📚 Documentação

| Documento | O quê |
|---|---|
| [docs/app.md](docs/app.md) | Arquitetura do app Flask |
| [DESIGN.md](DESIGN.md) | Design system, temas e painel do aluno |
| [docs/desktop.md](docs/desktop.md) | Shell Electron (app instalável) |
| [docs/banco_dados.md](docs/banco_dados.md) | Banco, RLS e modelo de segurança |
| [docs/rotas/](docs/rotas/) | Cada blueprint documentado |
| [docs/utils.md](docs/utils.md) · [docs/extensoes.md](docs/extensoes.md) | Utilitários e extensões Flask |
| [site/README.md](site/README.md) | Página pública de confirmação de e-mail (GitHub Pages) |
| [tests/README.md](tests/README.md) | Especificação da suíte de testes |
| [PRODUCT.md](PRODUCT.md) | Fatos confirmados do produto |

<a id="contribuicao"></a>
## 🤝 Contribuição

Issues e pull requests são bem-vindos! Antes de mexer no modelo de dados, leia [docs/banco_dados.md](docs/banco_dados.md) (as policies RLS são o coração da segurança) e rode a suíte de testes — ela não exige nenhum serviço externo.

<a id="licenca"></a>
## 📄 Licença

Distribuído sob a licença **MIT** — veja [LICENSE](LICENSE) para detalhes.
