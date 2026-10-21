# Gabaritei Aluno — Shell Electron (desktop/)

## Arquitetura
O app do aluno é o **Flask de sempre** (`app.py`, porta 5000, host `127.0.0.1`); o Electron é apenas a "casca" desktop:

```
desktop/main.js (shell Electron)
   └── spawn backend ──► Dev: venv/Scripts/python.exe app.py
                   └──► Prod: resources/backend/GabariteiAluno.exe (PyInstaller)
   └── BrowserWindow ──► http://127.0.0.1:5000/aluno/login
```

- **Pasta `desktop/` contém ZERO código do produto** — o backend do aluno continua sendo o repo Flask (que já nasce sem nenhum arquivo do painel admin).
- `Menu.setApplicationMenu(null)` + `autoHideMenuBar` → janela limpa de app.
- Links externos (`window.open`, `_blank`) abrem no navegador do sistema via `shell.openExternal`.

## Segurança do bundle
- A `SUPABASE_ANON_KEY` é **pública por design** e embutida no `main.js` — protegida pelas policies RLS (`rls_policies_aluno` + `security_hardening_p1`). A **service_role jamais entra no bundle**: o app do aluno importa exclusivamente `banco_dados_aluno.py`.
- O `APP_TOKEN` (header `x-app-token` exigido pelas policies de ESCRITA — migration `rls_header_app_aluno`) fica em `desktop/token.local.js` (gitignored; template em `desktop/token.example.js`) e é injetado no env do processo spawnado — nunca no git.
- As credenciais chegam ao backend via **variáveis de ambiente do processo spawnado** (não via `.env` no pacote) — `load_dotenv()` não sobrescreve variáveis existentes, então o que o shell passa vence.
- `FLASK_SECRET_KEY` é persistente (`userData/secret.key`, gerada 1x na primeira execução): a sessão Flask sobrevive entre execuções — necessária porque o login do Auth é lembrado via refresh token. Não há segredo estático no binário (a chave nasce na máquina do usuário).

## Desenvolvimento
```powershell
cd desktop
npm install        # 1ª vez (baixa o Electron)
npm start          # spawna o Flask do venv e abre a janela
```
Requisitos: venv do repo ativo em `../venv` (o shell usa `venv/Scripts/python.exe` direto).

## Build (fases)
1. **Backend**: PyInstaller do `app.py` → `dist_backend/GabariteiAluno.exe` (inclui `rotas/`, `templates/`, `static/`, `utils.py`, `extensoes.py`, `modelos.py`, `banco_dados_aluno.py`; o `APP_TOKEN` do bundle vem do `token.local.js` no build). *(a implementar)*
2. **Instalador**: `npm run dist` → electron-builder NSIS (`desktop/dist/GabariteiAluno-Setup-x.y.z.exe`), que embala o shell + `extraResources` do backend. *(a implementar)*