// ============================================================
// Gabaritei Aluno — shell Electron do app do aluno (Flask local)
// ------------------------------------------------------------
// Dev:      spawna o Python do venv do repo com app.py
// Prod:     spawna o backend empacotado (PyInstaller) de resources/backend
//
// Segurança:
// - A SUPABASE_ANON_KEY aqui embutida é PÚBLICA por design (protegida por
//   RLS na migration rls_policies_aluno). A service_role NUNCA entra no
//   bundle — o app do aluno importa apenas banco_dados_aluno.py.
// - FLASK_SECRET_KEY é persistente em app.getPath('userData')/secret.key:
//   a sessão (login lembrado, refresh token do Auth) sobrevive entre
//   execuções do app — antes era aleatória a cada boot e a sessão morria.
// - O backend escuta apenas 127.0.0.1 (host do app.py).
// ============================================================

const { app, BrowserWindow, Menu, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const crypto = require('crypto');
const fs = require('fs');

// --- Configuração (anon key pública, protegida por RLS) ---
const SUPABASE_URL = 'https://ivhuaevrrkrnagbqmnwc.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml2aHVhZXZycmtybmFnYnFtbndjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI2NTIzNDcsImV4cCI6MjA4ODIyODM0N30.6_XLnAn2XGNtP5bTQpWVMWVs600cES16rOGd_JtOYcE';
// Token de app: as policies de ESCRITA do aluno exigem o header x-app-token
// (validado pela função public.eh_app_aluno do banco). NUNCA vai no git —
// fica em desktop/token.local.js (gitignored; copie de token.example.js).
// Rotação = regenerar token_hex(32) + migration no banco + token.local.js + .env de dev.
let APP_TOKEN;
try {
  ({ APP_TOKEN } = require('./token.local.js'));
} catch (e) {
  console.error('[shell] ERRO: desktop/token.local.js ausente — copie desktop/token.example.js para desktop/token.local.js e preencha o APP_TOKEN.');
  process.exit(1);
}

const HOST = '127.0.0.1';
const PORTA = 5000;

const ehDev = !app.isPackaged;

let backend = null;
let janela = null;

// Sessões que sobrevivem ao fechar/abrir: a secret key é gerada 1x e fica em
// app.getPath('userData')/secret.key — o login do Auth é lembrado entre boots.
function secretKeyPersistente() {
  const p = path.join(app.getPath('userData'), 'secret.key');
  try {
    return fs.readFileSync(p, 'utf8').trim();
  } catch (e) {
    const k = crypto.randomBytes(32).toString('hex');
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, k);
    return k;
  }
}

function configBackend() {
  if (ehDev) {
    return {
      cmd: path.join(__dirname, '..', 'venv', 'Scripts', 'python.exe'),
      args: ['app.py'],
      cwd: path.join(__dirname, '..'),
    };
  }
  const exe = path.join(process.resourcesPath, 'backend', 'GabariteiAluno.exe');
  return { cmd: exe, args: [], cwd: path.dirname(exe) };
}

function iniciarBackend() {
  const { cmd, args, cwd } = configBackend();
  console.log(`[shell] backend (dev=${ehDev}): ${cmd} ${args.join(' ')}`);
  backend = spawn(cmd, args, {
    cwd,
    windowsHide: true,
    env: {
      ...process.env,
      SUPABASE_URL,
      SUPABASE_ANON_KEY,
      FLASK_SECRET_KEY: secretKeyPersistente(),
      FLASK_DEBUG: 'false',
      APP_TOKEN,
    },
  });
  backend.stdout.on('data', (d) => console.log(`[backend] ${d}`.trimEnd()));
  backend.stderr.on('data', (d) => console.error(`[backend] ${d}`.trimEnd()));
  backend.on('exit', (code) => console.log(`[backend] encerrou com codigo ${code}`));
}

function esperarServidor(maxTentativas = 90) {
  return new Promise((resolve, reject) => {
    const tentar = (n) => {
      const req = http.get({ host: HOST, port: PORTA, path: '/aluno/login', timeout: 2000 }, (res) => {
        res.resume();
        resolve();
      });
      const falhou = () => {
        if (n <= 0) return reject(new Error('backend nao respondeu no prazo'));
        setTimeout(() => tentar(n - 1), 1000);
      };
      req.on('error', falhou);
      req.on('timeout', () => { req.destroy(); falhou(); });
    };
    tentar(maxTentativas);
  });
}

async function criarJanela() {
  janela = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 700,
    show: false,
    autoHideMenuBar: true,
    title: 'Gabaritei Aluno',
    backgroundColor: '#ffffff',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  janela.once('ready-to-show', () => janela.show());
  janela.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
  await janela.loadURL(`http://${HOST}:${PORTA}/aluno/login`);
}

app.whenReady().then(async () => {
  Menu.setApplicationMenu(null);
  iniciarBackend();
  try {
    await esperarServidor();
    await criarJanela();
  } catch (e) {
    console.error(`[shell] ERRO: ${e.message}`);
    app.quit();
  }
});

app.on('window-all-closed', () => app.quit());
app.on('before-quit', () => {
  if (backend && !backend.killed) backend.kill();
});