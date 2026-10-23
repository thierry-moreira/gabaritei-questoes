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

Pipeline validado de ponta a ponta (out/2026): backend PyInstaller sobe sozinho com HTTP 200 e o instalador NSIS instala shell + backend; o `main.js` detecta `app.isPackaged`, spawna `resources/backend/GabariteiAluno.exe`, o BrowserWindow carrega `http://127.0.0.1:5000/aluno/login` e o backend morre junto no encerramento (sem órfãos).

1. **Backend — PyInstaller** (a partir da raiz do repo, com o venv ativo):
   ```powershell
   pip install pyinstaller
   venv\Scripts\pyinstaller --noconfirm --clean --name GabariteiAluno `
     --distpath dist_backend --workpath build_backend `
     --add-data "templates;templates" --add-data "static;static" app.py
   ```
   Gera `dist_backend/GabariteiAluno/GabariteiAluno.exe` (+ `_internal/`). O exe **mantém o console** de propósito: o shell o spawna com `windowsHide: true` (nenhuma janela aparece) e captura os logs do Flask pelos pipes — com `--noconsole` o `sys.stdout` seria `None` e os `print()` das rotas estourariam.
   - `templates/` e `static/` entram via `--add-data`; o `.env` **não** entra — as credenciais chegam pelas variáveis de ambiente do shell.
   - WeasyPrint segue o comportamento do dev: se o GTK/Pango não estiver na máquina, `rotas/simulado.py` já degrada com `HTML = None` (PDF indisponível com mensagem amigável) — nenhum crash.
   - Teste standalone (simula o env que o shell passa): suba o exe com `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `APP_TOKEN`, `FLASK_SECRET_KEY` e `GABARITEI_LOCAL_DIR` no env e confira `http://127.0.0.1:5000/aluno/login` → 200.

2. **Instalador — electron-builder NSIS**:
   ```powershell
   cd desktop
   npm install        # 1ª vez (baixa o Electron)
   npm run dist
   ```
   Gera `desktop/dist/GabariteiAluno-Setup-x.y.z.exe` (+ `win-unpacked/` portátil). O `extraResources` copia `dist_backend/GabariteiAluno/` para `resources/backend/` (o caminho que o `main.js` espera), e o `token.local.js` entra no `app.asar` por design — o `main.js` o requer em runtime para injetar o `APP_TOKEN` no env do backend.

Futuras melhorias: ícone `.ico` próprio (hoje o instalador usa o ícone padrão do Electron — converter `static/icone.webp` em `.ico` 256px e apontar em `build.icon`); code signing; `win-unpacked` como release portátil.