# -*- coding: utf-8 -*-
"""
banco_local.py — armazenamento LOCAL (SQLite) das configurações sensíveis do
aluno que jamais devem ir para o Supabase.

Hoje guarda apenas a chave de API de IA (BYOK — Bring Your Own Key):
provedor + modelo + chave do provedor escolhido pelo próprio aluno em
Configurações da conta.

Decisões de segurança:
- O arquivo vive no userData do app (Electron passa GABARITEI_LOCAL_DIR) ou,
  em dev direto no terminal, em %APPDATA%\\Gabaritei Aluno (Windows) ou
  ~/.gabaritei (outros SOs).
- No Windows a chave é cifrada com a DPAPI (CryptProtectData/CryptUnprotectData
  via ctypes — zero dependências novas): o conteúdo só é legível pelo mesmo
  usuário do Windows que gravou. Fora do Windows há fallback base64 com aviso
  — a chave continua só nesta máquina, mas sem cifração nativa do SO.
- Nada daqui é sincronizado com o Supabase; a UI devolve apenas a máscara
  (ex: 'sk-1…9f2c') — nunca a chave completa.
"""
import base64
import logging
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_PREFIXO_DPAPI = "v1:dpapi:"
_PREFIXO_PLAIN = "v1:plain:"


def _caminho_banco() -> Path:
    """Diretório do banco local: env do Electron (userData) → AppData → home."""
    env_dir = os.getenv("GABARITEI_LOCAL_DIR")
    if env_dir:
        base = Path(env_dir)
    elif sys.platform == "win32":
        appdata = os.getenv("APPDATA") or str(Path.home())
        base = Path(appdata) / "Gabaritei Aluno"
    else:
        base = Path.home() / ".gabaritei"
    base.mkdir(parents=True, exist_ok=True)
    return base / "config_local.db"


def _conectar() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_caminho_banco()))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS config_ia (
            id_usuario     TEXT PRIMARY KEY,
            provedor       TEXT NOT NULL,
            modelo         TEXT NOT NULL,
            chave_cifrada  TEXT NOT NULL,
            atualizado_em  TEXT NOT NULL
        )
        """
    )
    return conn


# ----------------------------------------------------------------------------
# Cifração da chave (DPAPI no Windows; fallback base64 em outros SOs)
# ----------------------------------------------------------------------------
if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes

    class _DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", ctypes.wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_char)),
        ]

    def _cifrar_bytes(dados: bytes) -> str:
        buf = ctypes.create_string_buffer(dados, len(dados))
        blob_in = _DATA_BLOB(len(dados), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
        blob_out = _DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
        )
        if not ok:
            raise OSError("CryptProtectData (DPAPI) falhou")
        try:
            return _PREFIXO_DPAPI + base64.b64encode(
                ctypes.string_at(blob_out.pbData, blob_out.cbData)
            ).decode("ascii")
        finally:
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)

    def _decifrar_para_bytes(repr_cifrada: str) -> bytes:
        dados = base64.b64decode(repr_cifrada[len(_PREFIXO_DPAPI):])
        buf = ctypes.create_string_buffer(dados, len(dados))
        blob_in = _DATA_BLOB(len(dados), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
        blob_out = _DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
        )
        if not ok:
            raise OSError("CryptUnprotectData (DPAPI) falhou")
        try:
            return ctypes.string_at(blob_out.pbData, blob_out.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
else:
    _AVISADO_PLAIN = False

    def _cifrar_bytes(dados: bytes) -> str:
        global _AVISADO_PLAIN
        if not _AVISADO_PLAIN:
            logger.warning(
                "⚠️ SO sem DPAPI: a chave de IA será gravada apenas obstruída "
                "(base64) neste dispositivo local."
            )
            _AVISADO_PLAIN = True
        return _PREFIXO_PLAIN + base64.b64encode(dados).decode("ascii")

    def _decifrar_para_bytes(repr_cifrada: str) -> bytes:
        return base64.b64decode(repr_cifrada[len(_PREFIXO_PLAIN):])


def _cifrar_chave(chave: str) -> str:
    return _cifrar_bytes(chave.encode("utf-8"))


def _decifrar_chave(chave_cifrada: str) -> str | None:
    try:
        if chave_cifrada.startswith(_PREFIXO_DPAPI):
            if sys.platform != "win32":
                return None  # blob DPAPI em SO não-Windows: ilegível por design
            return _decifrar_para_bytes(chave_cifrada).decode("utf-8")
        if chave_cifrada.startswith(_PREFIXO_PLAIN):
            return _decifrar_para_bytes(chave_cifrada).decode("utf-8")
        return None
    except Exception as e:
        logger.error(f"❌ Falha ao decifrar a chave de IA local: {e}")
        return None


# ----------------------------------------------------------------------------
# API pública
# ----------------------------------------------------------------------------
def salvar_config_ia(id_usuario, provedor: str, modelo: str, chave: str) -> None:
    """Grava (ou substitui) a configuração de IA do aluno logado."""
    agora = datetime.now(timezone.utc).isoformat()
    conn = _conectar()
    try:
        conn.execute(
            """
            INSERT INTO config_ia (id_usuario, provedor, modelo, chave_cifrada, atualizado_em)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id_usuario) DO UPDATE SET
                provedor      = excluded.provedor,
                modelo        = excluded.modelo,
                chave_cifrada = excluded.chave_cifrada,
                atualizado_em = excluded.atualizado_em
            """,
            (str(id_usuario), provedor, modelo, _cifrar_chave(chave), agora),
        )
        conn.commit()
    finally:
        conn.close()


def ler_config_ia(id_usuario) -> dict | None:
    """Devolve {'provedor','modelo','chave'} do aluno, ou None se não houver."""
    try:
        conn = _conectar()
        try:
            linha = conn.execute(
                "SELECT provedor, modelo, chave_cifrada FROM config_ia WHERE id_usuario = ?",
                (str(id_usuario),),
            ).fetchone()
        finally:
            conn.close()
    except sqlite3.Error as e:
        logger.error(f"❌ Erro no banco local de configuração: {e}")
        return None
    if not linha:
        return None
    chave = _decifrar_chave(linha[2])
    if not chave:
        return None
    return {"provedor": linha[0], "modelo": linha[1], "chave": chave}


def remover_config_ia(id_usuario) -> bool:
    """Apaga a configuração de IA do aluno. True se havia registro."""
    conn = _conectar()
    try:
        cur = conn.execute("DELETE FROM config_ia WHERE id_usuario = ?", (str(id_usuario),))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def mascarar_chave(chave: str) -> str:
    """Máscara segura para exibição: 'sk-11…9f2c'. Nunca expõe o miolo."""
    if not chave:
        return ""
    if len(chave) <= 8:
        return "••••••"
    return f"{chave[:4]}…{chave[-4:]}"

