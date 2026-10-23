# -*- coding: utf-8 -*-
"""
provedores_ia.py — camada BYOK (Bring Your Own Key) de IA do app do aluno.

Cada aluno usa a PRÓPRIA chave de API (OpenAI, Google Gemini ou Anthropic),
configurada em Configurações da conta e guardada apenas localmente
(banco_local.py — SQLite + DPAPI; nunca no Supabase).

PROMPTS E PARÂMETROS CONGELADOS: este módulo é apenas o "transporte" das
chamadas. O conteúdo do system prompt, a temperatura e os demais parâmetros
continuam definidos nas rotas (rotas/questao.py) exatamente como calibrados:
- /api/ia_explica      → temperature=0.0, top_p=0.1, presence/frequency=0.0
- /api/ia/gerar_estudo → TEMPERATURE_GPT = 0.3
Nada aqui altera o conteúdo enviado aos modelos.
"""
import base64
import logging
import mimetypes
import re
from typing import Any

import requests
from openai import OpenAI, BadRequestError

from banco_local import ler_config_ia

logger = logging.getLogger(__name__)

# Herdada de extensoes.py (era TEMPERATURE_GPT) — valor calibrado do produto.
TEMPERATURE_GPT = 0.3

# Mensagem padrão quando o aluno ainda não configurou a própria chave.
MSG_NAO_CONFIGURADA = (
    "IA não configurada — adicione sua chave de API em Configurações da conta "
    "(card Inteligência Artificial)."
)

# ----------------------------------------------------------------------------
# Provedores suportados e modelos pré-configurados (listas oficiais do produto)
# ----------------------------------------------------------------------------
PROVEDORES: dict[str, dict[str, Any]] = {
    "openai": {
        "nome": "OpenAI",
        "modelos": [
            "gpt-6.1-sol",
            "gpt-5.6-luna",
            "gpt-5.6-terra",
            "gpt-6-sol",
            "gpt-5.2-2025-12-11",
            "gpt-5-2025-08-07",
            "gpt-5.4-2026-03-05",
        ],
        "modelo_padrao": "gpt-5.6-luna",
        "link_chave": "https://platform.openai.com/api-keys",
        "api_base": "https://api.openai.com/v1",
    },
    "gemini": {
        "nome": "Google Gemini",
        "modelos": [
            "gemini-4-argon",
            "gemini-3.8-flash",
            "gemini-3.1-pro-preview",
            "gemini-3.5-flash-lite",
        ],
        "modelo_padrao": "gemini-4-argon",
        "link_chave": "https://aistudio.google.com/apikey",
        # Endpoint OpenAI-compatível do Google: mesmo SDK, só muda a base URL.
        "api_base": "https://generativelanguage.googleapis.com/v1beta/openai",
    },
    "anthropic": {
        "nome": "Anthropic Claude",
        "modelos": [
            "claude-haiku-5-5",
            "claude-sonnet-5-5",
        ],
        "modelo_padrao": "claude-sonnet-5-5",
        "link_chave": "https://console.anthropic.com/settings/keys",
        "api_base": "https://api.anthropic.com",
    },
}

# Parâmetros de geração aceitos por provedor — os demais são omitidos com log
# (ex.: presence/frequency_penalty não existem na Anthropic; o endpoint
# OpenAI-compat do Gemini aceita temperature/top_p, mas rejeita os penalties
# com 400 "Unknown name ...: Cannot find field").
_PARAMETROS_SUPORTADOS = {
    "openai": {"temperature", "top_p", "presence_penalty", "frequency_penalty"},
    "gemini": {"temperature", "top_p"},
    "anthropic": {"temperature", "top_p"},
}

_TIMEOUT_HTTP = 120                    # gerações pedagógicas podem demorar
_TIMEOUT_PING = 15                     # validação de chave/modelo (GET gratuito)
_TIMEOUT_IMAGEM = 20                    # download de imagem p/ Anthropic (base64)
_MAX_BYTES_IMAGEM = 8 * 1024 * 1024     # imagens acima de 8 MB são ignoradas
# A API Messages da Anthropic exige max_tokens; 8192 cobre as explicações
# pedagógicas mais longas sem truncar (parâmetro de transporte, não de estilo).
_MAX_TOKENS_ANTHROPIC = 8192


class ErroIA(RuntimeError):
    """Erro da camada de IA com código amigável p/ a UI."""

    def __init__(self, mensagem: str, codigo: str = "falha_ia"):
        super().__init__(mensagem)
        self.codigo = codigo


def ia_configurada(id_usuario) -> bool:
    """True se o aluno logado tem chave de IA salva localmente."""
    return ler_config_ia(id_usuario) is not None


def _filtrar_parametros(provedor: str, kwargs: dict) -> dict:
    """Mantém apenas os parâmetros que o provedor suporta."""
    suportados = _PARAMETROS_SUPORTADOS.get(provedor, set())
    filtrados = {k: v for k, v in kwargs.items() if k in suportados and v is not None}
    omitidos = [k for k in kwargs if k not in suportados and kwargs[k] is not None]
    if omitidos:
        logger.info(
            f"ℹ️ Parâmetros não suportados por '{provedor}' e omitidos: {', '.join(omitidos)}"
        )
    return filtrados


# ----------------------------------------------------------------------------
# Chamada principal
# ----------------------------------------------------------------------------
def chamar_ia(
    id_usuario,
    system_prompt: str,
    conteudo: list,
    temperature: float = 0.3,
    top_p: float | None = None,
    presence_penalty: float | None = None,
    frequency_penalty: float | None = None,
) -> str:
    """
    Gera texto com o provedor configurado pelo próprio aluno (BYOK).

    `conteudo` é a mesma lista multimodal montada pelas rotas
    ([{"type":"text","text":...}, {"type":"image_url","image_url":{"url":...}}]).
    Devolve somente o texto da resposta — o fluxo das rotas (cache, sanitização
    e gravação no Supabase) permanece idêntico ao original.
    """
    config = ler_config_ia(id_usuario)
    if not config:
        raise ErroIA(MSG_NAO_CONFIGURADA, "sem_config")

    provedor = config["provedor"]
    modelo = config["modelo"]
    chave = config["chave"]

    params = _filtrar_parametros(
        provedor,
        {
            "temperature": temperature,
            "top_p": top_p,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
        },
    )

    if provedor == "openai":
        return _chamar_openai_compat(
            chave, modelo, system_prompt, conteudo, params,
            role_system="developer", base_url=None,
        )
    if provedor == "gemini":
        return _chamar_openai_compat(
            chave, modelo, system_prompt, conteudo, params,
            role_system="system", base_url=PROVEDORES["gemini"]["api_base"] + "/",
        )
    if provedor == "anthropic":
        return _chamar_anthropic(chave, modelo, system_prompt, conteudo, params)
    raise ErroIA(f"Provedor de IA desconhecido: {provedor}", "sem_config")


def _extrair_unknown_name(texto: str) -> str | None:
    """Formato Google: 'Unknown name "frequency_penalty": Cannot find field.'"""
    m = re.search(r'Unknown name\s+"([^"]+)"', texto or "")
    return m.group(1) if m else None


def _param_rejeitado(e: Exception) -> str | None:
    """
    Extrai o parâmetro rejeitado pelo MODELO/endpoint de um erro 400.
    Reconhece dois formatos de provedor:
    - OpenAI: {'error': {'code': 'unsupported_value', 'param': 'temperature'}}
    - Google/Gemini (compat): {'error': {'status': 'INVALID_ARGUMENT', 'details': [
        {'fieldViolations': [{'description': 'Unknown name "x": ...'}]}]}}
    """
    # 1) Body estruturado
    body = getattr(e, "body", None)
    if isinstance(body, dict):
        erro = body.get("error") if isinstance(body.get("error"), dict) else body
        code = str(erro.get("code", ""))
        param = erro.get("param")
        if param and code in ("unsupported_value", "unsupported_parameter"):
            return str(param)
        # Formato Google/Gemini: fieldViolations
        for detalhe in erro.get("details") or []:
            if not isinstance(detalhe, dict):
                continue
            for violacao in detalhe.get("fieldViolations") or []:
                if isinstance(violacao, dict):
                    nome = _extrair_unknown_name(str(violacao.get("description", "")))
                    if nome:
                        return nome
    # 2) Fallback: parse do texto da exceção
    texto = str(e)
    if "unsupported_value" in texto or "unsupported_parameter" in texto:
        m = re.search(r"'param':\s*'([^']+)'", texto)
        if m:
            return m.group(1)
    return _extrair_unknown_name(texto)


def _chamar_openai_compat(
    chave: str, modelo: str, system_prompt: str, conteudo: list,
    params: dict, role_system: str, base_url: str | None,
) -> str:
    """
    OpenAI e Gemini (endpoint OpenAI-compatível do Google) — mesmo SDK.

    Os parâmetros calibrados vão SEMPRE na 1ª tentativa; se o modelo não
    suportar algum (modelos de raciocínio rejeitam temperature/top_p/penalties
    com 400 'unsupported_value'), a camada o omite e repete a chamada —
    máx. 2 repetições.
    """
    client = OpenAI(api_key=chave, base_url=base_url)
    mensagens = [
        {"role": role_system, "content": system_prompt},
        {"role": "user", "content": conteudo},
    ]
    tentativas = dict(params)  # cópia: os calibrados nunca são mutados
    for _ in range(3):  # 1ª chamada + até 2 ajustes
        try:
            response = client.chat.completions.create(
                model=modelo, messages=mensagens, **tentativas
            )
            return response.choices[0].message.content or ""
        except BadRequestError as e:
            param = _param_rejeitado(e)
            if not param or param not in tentativas:
                raise _traduzir_erro_sdk(e)
            logger.info(
                f"ℹ️ Modelo '{modelo}' não suporta '{param}' — repetindo com o "
                f"valor default do modelo (modelos de raciocínio preservam o "
                f"determinismo pela própria cadeia de raciocínio)."
            )
            tentativas.pop(param)
        except Exception as e:
            raise _traduzir_erro_sdk(e)
    raise ErroIA("O modelo rejeitou os parâmetros de geração.", "param_invalido")


def _traduzir_erro_sdk(e: Exception) -> Exception:
    """Converte erros do SDK OpenAI/SDK Gemini-compat em ErroIA amigável."""
    nome = type(e).__name__
    texto = str(e)
    if nome == "AuthenticationError" or "401" in texto or "API key not valid" in texto:
        return ErroIA("Chave de API inválida para o provedor escolhido.", "chave_invalida")
    if nome == "NotFoundError" or ("model" in texto.lower() and "not found" in texto.lower()):
        return ErroIA("Modelo não encontrado no provedor. Ajuste em Configurações da conta.", "modelo_invalido")
    if nome in ("APITimeoutError", "APIConnectTimeoutError"):
        return ErroIA("Tempo esgotado ao contatar o provedor de IA. Tente novamente.", "falha_rede")
    if "402" in texto or "insufficient_quota" in texto or "billing" in texto.lower():
        # Falta de crédito: 402 billing_error (Anthropic), insufficient_quota (OpenAI)
        return ErroIA(
            "Sua conta no provedor está sem créditos/billing ativo (saldo zerado ou "
            "limite de gastos atingido). Adicione créditos e tente novamente.",
            "sem_credito",
        )
    if nome == "RateLimitError":
        return ErroIA("Limite de requisições da sua chave de IA atingido. Tente em instantes.", "rate_limit")
    return e


def _baixar_imagem_base64(url: str) -> dict | None:
    """
    Baixa a imagem e devolve o bloco nativo da Anthropic
    ({"type":"image","source":{"type":"base64",...}}). Falha → None (a geração
    prossegue sem a imagem, como o fluxo já tolera com outros provedores).
    """
    try:
        r = requests.get(url, timeout=_TIMEOUT_IMAGEM)
        r.raise_for_status()
        if len(r.content) > _MAX_BYTES_IMAGEM:
            logger.warning(f"⚠️ Imagem > 8 MB ignorada na chamada Anthropic: {url[:80]}")
            return None
        media_type = r.headers.get("Content-Type", "").split(";")[0].strip()
        if not media_type or media_type in ("application/octet-stream", "binary/octet-stream"):
            media_type = mimetypes.guess_type(url)[0] or "image/png"
        if media_type not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
            logger.warning(f"⚠️ Tipo de imagem não suportado pela Anthropic ({media_type}) — ignorada.")
            return None
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64.b64encode(r.content).decode("ascii"),
            },
        }
    except Exception as e:
        logger.warning(f"⚠️ Falha ao baixar imagem p/ Anthropic (seguindo sem ela): {e}")
        return None


def _chamar_anthropic(chave: str, modelo: str, system_prompt: str, conteudo: list, params: dict) -> str:
    """Anthropic Messages API (via requests — sem endpoint OpenAI-compat)."""
    blocos: list[dict] = []
    for parte in conteudo:
        if parte.get("type") == "text":
            blocos.append({"type": "text", "text": parte.get("text", "")})
        elif parte.get("type") == "image_url":
            url = (parte.get("image_url") or {}).get("url", "")
            bloco = _baixar_imagem_base64(url) if url else None
            if bloco:
                blocos.append(bloco)

    tentativas = dict(params)  # cópia: os calibrados nunca são mutados
    for _ in range(3):  # 1ª chamada + até 2 ajustes de parâmetro rejeitado
        payload: dict[str, Any] = {
            "model": modelo,
            "max_tokens": _MAX_TOKENS_ANTHROPIC,
            "system": system_prompt,
            "messages": [{"role": "user", "content": blocos or [{"type": "text", "text": ""}]}],
        }
        payload.update(tentativas)  # temperature / top_p (únicos suportados)

        try:
            r = requests.post(
                f"{PROVEDORES['anthropic']['api_base']}/v1/messages",
                json=payload,
                headers={
                    "x-api-key": chave,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                timeout=_TIMEOUT_HTTP,
            )
        except requests.RequestException:
            raise ErroIA("Falha de conexão com a Anthropic. Verifique sua internet.", "falha_rede")

        if r.status_code == 401:
            raise ErroIA("Chave da Anthropic inválida.", "chave_invalida")
        if r.status_code == 404:
            raise ErroIA("Modelo não encontrado na Anthropic. Ajuste em Configurações da conta.", "modelo_invalido")
        if r.status_code == 429:
            raise ErroIA("Limite de requisições da sua chave da Anthropic atingido.", "rate_limit")
        if r.status_code == 402:
            # billing_error: a Anthropic exige créditos ativos (sem free tier p/ API)
            raise ErroIA(
                "Sua conta da Anthropic não tem créditos/billing ativo — adicione "
                "créditos em https://console.anthropic.com e tente novamente.",
                "sem_credito",
            )

        if r.status_code == 400:
            detalhe: dict = {}
            param = None
            try:
                detalhe = r.json().get("error", {}) or {}
                if detalhe.get("type") == "invalid_request_error":
                    param = detalhe.get("param")
            except Exception:
                pass
            if param and param in tentativas:
                logger.info(
                    f"ℹ️ Modelo '{modelo}' não suporta '{param}' — repetindo com o valor default."
                )
                tentativas.pop(param)
                continue
            raise ErroIA(f"Erro da Anthropic (HTTP 400): {detalhe.get('message', '')}", "falha_ia")

        if r.status_code >= 400:
            detalhe = ""
            try:
                detalhe = r.json().get("error", {}).get("message", "")
            except Exception:
                pass
            raise ErroIA(f"Erro da Anthropic (HTTP {r.status_code}): {detalhe}", "falha_ia")

        try:
            dados = r.json()
            texto = "".join(
                b.get("text", "") for b in dados.get("content", []) if b.get("type") == "text"
            )
        except Exception as e:
            raise ErroIA(f"Resposta inválida da Anthropic: {e}", "falha_ia")
        if not texto.strip():
            raise ErroIA("O provedor devolveu uma resposta vazia.", "resposta_vazia")
        return texto

    raise ErroIA("O modelo rejeitou os parâmetros de geração.", "param_invalido")


# ----------------------------------------------------------------------------
# Validação de chave + modelo (ping gratuito — GET em /models, sem gastar tokens)
# ----------------------------------------------------------------------------
def _ping(url: str, headers: dict) -> tuple[bool, str]:
    try:
        r = requests.get(url, headers=headers, timeout=_TIMEOUT_PING)
    except requests.RequestException:
        return False, "Não foi possível contatar o provedor. Verifique sua internet."
    if r.status_code in (401, 403):
        return False, "Chave de API inválida."
    if r.status_code == 404:
        return False, "Modelo não encontrado no provedor."
    if r.status_code == 402:
        return False, "Sua conta no provedor não tem créditos/billing ativo. Adicione créditos e tente novamente."
    if r.status_code != 200:
        return False, f"Erro ao validar no provedor (HTTP {r.status_code})."
    return True, ""


def testar_chave(provedor: str, chave: str, modelo: str) -> tuple[bool, str]:
    """
    Valida a chave E o modelo do provedor com 2 GETs gratuitos
    (listar modelos + recuperar o modelo específico). Não gera tokens.
    """
    if provedor == "openai":
        headers = {"Authorization": f"Bearer {chave}"}
        base = PROVEDORES["openai"]["api_base"]
    elif provedor == "gemini":
        headers = {"Authorization": f"Bearer {chave}"}
        base = PROVEDORES["gemini"]["api_base"]
    elif provedor == "anthropic":
        headers = {"x-api-key": chave, "anthropic-version": "2023-06-01"}
        base = PROVEDORES["anthropic"]["api_base"]
    else:
        return False, "Provedor não suportado."

    ok, motivo = _ping(f"{base}/models", headers)
    if not ok:
        return False, motivo
    return _ping(f"{base}/models/{modelo}", headers)
