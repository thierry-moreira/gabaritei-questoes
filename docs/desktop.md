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

## Build (pipeline único: `desktop\build.ps1`)

```powershell
powershell -ExecutionPolicy Bypass -File desktop\build.ps1
```

Fases (idempotentes — o runtime GTK baixa apenas na 1ª vez):

1. **Runtime GTK portátil** — baixa o *GTK-for-Windows-Runtime-Installer* (tschoonj, LGPL, 47 MB) para `build_gtk/runtime` (gitignored);
2. **Backend — PyInstaller** de `app.py` → `dist_backend/GabariteiAluno/GabariteiAluno.exe` (+ `_internal/`), com `templates/` e `static/` via `--add-data`. O exe mantém o console de propósito: o shell o spawna com `windowsHide` (nenhuma janela aparece) e captura os logs do Flask pelos pipes — com `--noconsole` o `sys.stdout` seria `None` e os `print()` das rotas estourariam. O `.env` não entra no bundle — as credenciais chegam pelas variáveis de ambiente do shell;
3. **GTK dentro do bundle** — copia `bin/` (80 DLLs) + `etc/fonts` para `dist_backend/GabariteiAluno/gtk/`;
4. **Instalador — electron-builder NSIS** → `desktop/dist/GabariteiAluno-Setup-x.y.z.exe` (+ `win-unpacked/` portátil). O `extraResources` leva o backend inteiro (com o GTK) para `resources/backend/`, e o `token.local.js` entra no `app.asar` por design — o `main.js` o requer em runtime para injetar o `APP_TOKEN` no env do backend.

### GTK portátil — PDF out-of-the-box

O PDF de simulados (WeasyPrint) funciona sem o usuário instalar nada: o runtime GTK (Pango/FontConfig/HarfBuzz) viaja **dentro do app**, em `resources/backend/gtk/`.

- O WeasyPrint carrega as DLLs com `LoadLibrary` simples, que **não resolve dependências transitivas** a partir da pasta delas. Solução: `rotas/simulado.py` **pré-carrega** as DLLs via `ctypes` (que usa `LOAD_WITH_ALTERED_SEARCH_PATH` e resolve as deps na própria pasta), na ordem de dependência — com os módulos já no processo, os `dlopen` por nome-base do WeasyPrint os reutilizam;
- O caminho vem de `GABARITEI_GTK_BIN` (injetado pelo `main.js`: `resources/backend/gtk/bin` em prod, o backend PyInstaller local em dev), com fallback auto-detect no exe empacotado (`sys.frozen`);
- `FONTCONFIG_FILE` aponta para o `fonts.conf` do bundle (que lista `C:\Windows\Fonts` via `WINDOWSFONTDIR`) — sem isso o fontconfig procuraria um caminho compilado do MSYS2 que não existe na máquina do usuário;
- Sem runtime presente (dev limpo/CI): tudo é no-op e o PDF degrada com `HTML = None` (mensagem amigável, nenhum crash).

Validado de ponta a ponta (out/2026): PDF real gerado com o runtime portátil; o app empacotado sobe com HTTP 200 e o WeasyPrint importa limpo, sem o aviso de GTK ausente.

Futuras melhorias: ícone `.ico` próprio (hoje o instalador usa o ícone padrão do Electron — converter `static/icone.webp` em `.ico` 256px e apontar em `build.icon`); code signing; `win-unpacked` como release portátil.