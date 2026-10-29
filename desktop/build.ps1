# ============================================================
# Build completo do app desktop do Gabaritei Questoes
#   1. Runtime GTK portatil (WeasyPrint/PDF) - baixa apenas 1x
#   2. Backend PyInstaller -> dist_backend/GabariteiAluno
#   3. Copia o GTK para dentro do bundle do backend
#   4. Instalador NSIS -> desktop/dist/GabariteiAluno-Setup-x.y.z.exe
# Uso:  powershell -ExecutionPolicy Bypass -File desktop\build.ps1
# ============================================================
$ErrorActionPreference = 'Stop'
$raiz = Split-Path $PSScriptRoot -Parent
Set-Location $raiz
Write-Host "==> Build do app desktop (raiz: $raiz)"

# --- 1. Runtime GTK portatil (LGPL - gtk-for-windows-runtime) ---
$gtkFonte = Join-Path $raiz 'build_gtk\runtime'
if (-not (Test-Path (Join-Path $gtkFonte 'bin'))) {
    Write-Host '==> [gtk] Runtime ausente: baixando o GTK-for-Windows-Runtime (47 MB)...'
    New-Item -ItemType Directory -Force (Join-Path $raiz 'build_gtk') | Out-Null
    $setup = Join-Path $raiz 'build_gtk\gtk3-runtime-setup.exe'
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri 'https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe' -OutFile $setup -UseBasicParsing
    $tmp = Join-Path $env:TEMP 'gabaritei-gtk-runtime'
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    Start-Process -FilePath $setup -ArgumentList "/S /D=$tmp" -Wait
    New-Item -ItemType Directory -Force $gtkFonte | Out-Null
    Copy-Item (Join-Path $tmp '*') $gtkFonte -Recurse -Force
    Write-Host '==> [gtk] Runtime extraido para build_gtk\runtime'
}

# --- 2. Backend PyInstaller ---
if (-not (Test-Path (Join-Path $raiz 'venv\Scripts\pyinstaller.exe'))) {
    Write-Host '==> [pyinstaller] instalando...'
    & (Join-Path $raiz 'venv\Scripts\pip.exe') install pyinstaller
}
Write-Host '==> [pyinstaller] empacotando o backend Flask (1-3 min)...'

# Python 3.15 (PEP 793): extensoes compiladas para a ABI estavel "abi3t"
# (ex.: cryptography/hazmat/bindings/_rust.pyd) carregam python3t.dll, que
# fica em <base>\abi3t-compat e NAO e copiado automaticamente pelo
# PyInstaller. Sem ele o backend morre no import com
# "ImportError: DLL load failed while importing _rust".
$pyBase = & (Join-Path $raiz 'venv\Scripts\python.exe') -c "import sys; print(sys.base_prefix)"
$python3t = Join-Path $pyBase 'abi3t-compat\python3t.dll'
$pyiArgs = @(
    '--noconfirm', '--clean', '--name', 'GabariteiAluno',
    '--distpath', 'dist_backend', '--workpath', 'build_backend',
    '--add-data', 'templates;templates',
    '--add-data', 'static;static'
)
if (Test-Path $python3t) {
    $pyiArgs += @('--add-binary', "$python3t;.")
} else {
    Write-Warning "python3t.dll nao encontrado em $python3t - extensoes abi3t (cryptography) podem falhar no backend empacotado."
}
& (Join-Path $raiz 'venv\Scripts\pyinstaller.exe') @pyiArgs app.py

# --- 3. GTK dentro do bundle do backend (o PyInstaller recria a pasta) ---
$gtkDest = Join-Path $raiz 'dist_backend\GabariteiAluno\gtk'
Write-Host '==> [gtk] copiando o runtime para o bundle do backend...'
New-Item -ItemType Directory -Force (Join-Path $gtkDest 'bin') | Out-Null
Copy-Item (Join-Path $gtkFonte 'bin\*') (Join-Path $gtkDest 'bin') -Force
if (Test-Path (Join-Path $gtkDest 'etc')) { Remove-Item (Join-Path $gtkDest 'etc') -Recurse -Force }
Copy-Item (Join-Path $gtkFonte 'etc') $gtkDest -Recurse -Force

# --- 4. Instalador NSIS ---
Write-Host '==> [electron-builder] gerando o instalador NSIS (2-5 min)...'
Push-Location (Join-Path $raiz 'desktop')
npm run dist
Pop-Location

Write-Host ''
Write-Host '==> PRONTO: desktop\dist\GabariteiAluno-Setup-*.exe (+ win-unpacked portatil)'
