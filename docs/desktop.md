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
- A janela roda com `contextIsolation: true`, `sandbox: true` e `nodeIntegration: false`. A única ponte com o renderer é `preload.js`, que expõe via `contextBridge` apenas `electronAPI.printToPDF()` e `electronAPI.isElectron`.

## Desenvolvimento
```powershell
cd desktop
npm install        # 1ª vez (baixa o Electron)
npm start          # spawna o Flask do venv e abre a janela
```
Requisitos: Python 3.15+, venv do repo ativo em `../venv` (o shell usa `venv/Scripts/python.exe` direto).

## Build (pipeline único: `desktop\build.ps1`)

```powershell
powershell -ExecutionPolicy Bypass -File desktop\build.ps1
```

Fases (idempotentes):

1. **Runtime GTK portátil (legado)** — baixa o *GTK-for-Windows-Runtime-Installer* (tschoonj, LGPL, 47 MB) para `build_gtk/runtime` (gitignored). O fluxo de PDF atual **não usa WeasyPrint/GTK**; a etapa permanece no script apenas como herança de builds anteriores;
2. **Backend — PyInstaller** de `app.py` → `dist_backend/GabariteiAluno/GabariteiAluno.exe` (+ `_internal/`), com `templates/` e `static/` via `--add-data`. O exe mantém o console de propósito: o shell o spawna com `windowsHide` (nenhuma janela aparece) e captura os logs do Flask pelos pipes — com `--noconsole` o `sys.stdout` seria `None` e os `print()` das rotas estourariam. O `.env` não entra no bundle — as credenciais chegam pelas variáveis de ambiente do shell;
3. **GTK dentro do bundle (legado)** — copia `bin/` (80 DLLs) + `etc/fonts` para `dist_backend/GabariteiAluno/gtk/`, embora o backend atual não carregue esse runtime;
4. **Instalador — electron-builder NSIS** → `desktop/dist/Gabaritei.exe` (+ `win-unpacked/` portátil). O `extraResources` leva o backend inteiro (com o GTK legado) para `resources/backend/`, e o `token.local.js` entra no `app.asar` por design — o `main.js` o requer em runtime para injetar o `APP_TOKEN` no env do backend.

> [!NOTE]
> O nome final do instalador vem de `nsis.artifactName` no `desktop/package.json` (`Gabaritei.${ext}` → `Gabaritei.exe`). A mensagem impressa ao final do `build.ps1` ainda cita o padrão antigo `GabariteiAluno-Setup-*.exe`.

### PDF e impressão (client-side)

O PDF de simulados não é renderizado no servidor. A rota `/simulado/<id_simulado>/pdf` monta a prova e entrega a **prévia navegável** (`templates/simulados/pdf_preview.html`, com `_pdf_corpo.html` e `static/css/pdf_style.css`), que inclui `static/js/imprimir_ou_pdf.js`:

- **Desktop (Electron)**: `preload.js` expõe `window.electronAPI.printToPDF()`; o `main.js` gera o arquivo com `webContents.printToPDF()` (A4, margens de 0.5 in, `printBackground: true`), salva em `os.tmpdir()` e abre no leitor padrão com `shell.openPath()`;
- **Navegador**: `imprimirOuPDF()` chama `window.print()`; o `@media print` esconde a barra de ações e expande a folha A4, e o aluno usa **"Salvar como PDF"**;
- **Atalhos**: o `main.js` adiciona o sufixo `GabariteiDesktop` ao User-Agent do renderer, intercepta `Ctrl+P` via `before-input-event` e substitui `window.print()` após cada navegação (`did-finish-load`) para disparar o PDF nativo em vez do diálogo de impressão do Chromium.

### Encerramento do backend

`before-quit` e `quit` chamam `matarBackend()`: no Windows, `taskkill /F /T /PID <pid>` encerra a árvore inteira de processos (o backend Python/PyInstaller pode ter filhos); no Linux/macOS, o fallback é `SIGTERM` no grupo. O `spawn` usa `windowsHide: true` para não abrir console.

Futuras melhorias: code signing; `win-unpacked` como release portátil.

O ícone do app (`static/icone.ico`) é aplicado ao executável e ao instalador via `build.icon` no `desktop/package.json`; o artefato do instalador é nomeado `Gabaritei.exe` via `nsis.artifactName`.