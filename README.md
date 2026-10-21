# Gabaritei Questões — app do aluno

Plataforma de estudo para concursos (questões, simulados, flashcards, resumos, cadernos e editais) em modelo **desktop local**. Software livre (licença MIT).

- **Conta real com e-mail e senha** (Supabase Auth): o progresso fica na nuvem, vinculado à conta — o mesmo aluno continua de onde parou em qualquer máquina.
- **100% offline-first no front**: backend Flask local + janela Electron.

## Arquitetura

| Camada | O quê |
|---|---|
| Backend | Flask (Python) em `127.0.0.1:5000` (`app.py`, 11 blueprints em `rotas/`) |
| Banco | Supabase (PostgreSQL) via **chave ANON pública** — toda a segurança vive em policies RLS |
| Shell | Electron (`desktop/main.js`) — spawna o backend e abre a janela |

**Modelo de segurança do cliente** (`docs/banco_dados.md`):
- Leitura de dados de estudo: liberada (questões, taxonomia, materiais — nada sensível).
- Escrita dos dados do aluno: exige o header `x-app-token` (migration `rls_header_app_aluno`) **e** a identidade do dono — `auth.uid()` amarrado a `usuarios.auth_id` (migrations `auth_usuario_e_policies` + `policies_para_authenticated`): mesmo que o token vaze, ninguém escreve dados de outro aluno.
- A chave `service_role` **nunca** faz parte deste app — gestão de conteúdo fica num painel separado.

## Setup (dev)

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # preencha URL, ANON key, APP_TOKEN e chave OpenAI
copy desktop\token.example.js desktop\token.local.js   # mesmo APP_TOKEN do .env
python app.py                   # http://127.0.0.1:5000
```

Shell Electron: `cd desktop; npm install; npm start`

## Testes

`rodar_testes.bat` ou `python -m unittest discover -s tests` — suíte 100% isolada (sem rede, sem banco real).

## Documentação

`docs/` — arquitetura do app (`app.md`), shell desktop (`desktop.md`), banco e RLS (`banco_dados.md`), rotas (`docs/rotas/`).

## Licença

MIT — veja [LICENSE](LICENSE).
