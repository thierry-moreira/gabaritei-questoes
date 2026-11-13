"""Gravações globais do app do aluno via Edge Function.

A migration ``secure_global_writes`` removeu INSERT/UPDATE/DELETE diretos das
tabelas globais (feedbacks, caches de IA) para os papéis ``anon`` e
``authenticated``. O app do aluno grava pela Edge Function
``secure-global-write``, que valida o JWT do aluno, o perfil, o payload e o
rate limit antes de persistir com ``service_role``.

Este módulo concentra o contrato HTTP para que as rotas Flask não precisem
conhecer detalhes da função nem duplicar o tratamento de erros.
"""

from __future__ import annotations

from typing import Any

import requests

from banco_dados_aluno import anon_key as _ANON_KEY
from banco_dados_aluno import sessao_atual as _sessao_atual
from banco_dados_aluno import url as _SUPABASE_URL

_TIMEOUT_SEGUNDOS = 15

_MENSAGENS_ERRO: dict[str, tuple[str, int]] = {
    "unauthorized": ("Sua sessão expirou. Entre novamente para continuar.", 401),
    "profile_required": ("Seu perfil de aluno não foi encontrado.", 403),
    "origin_not_allowed": ("Origem não autorizada para esta operação.", 403),
    "question_not_found": ("Questão não encontrada ou não publicada.", 404),
    "invalid_payload": ("Os dados enviados são inválidos.", 400),
    "payload_too_large": ("O conteúdo enviado é muito grande.", 413),
    "json_required": ("Formato de envio inválido.", 415),
    "method_not_allowed": ("Operação não permitida.", 405),
    "server_configuration_error": ("Serviço de gravação indisponível.", 503),
    "authorization_check_failed": ("Não foi possível validar seu perfil agora.", 503),
    "rate_limit_unavailable": ("Não foi possível validar o limite de envios agora.", 503),
    "question_check_failed": ("Não foi possível validar a questão agora.", 503),
    "write_failed": ("Não foi possível salvar o feedback no momento.", 503),
}


class ErroEscritaGlobal(Exception):
    """Falha ao persistir uma gravação global.

    ``mensagem`` é segura para exibir ao aluno e ``status`` é o código HTTP
    que a rota Flask deve devolver.
    """

    def __init__(self, mensagem: str, status: int = 502):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def escrever_global(operacao: str, **campos: Any) -> None:
    """Envia uma operação para a Edge Function ``secure-global-write``.

    Levanta ``ErroEscritaGlobal`` quando a sessão do aluno não está
    disponível, a função rejeita o payload ou a gravação falha.
    """
    sessao = _sessao_atual()
    token = getattr(sessao, "access_token", None) if sessao else None
    if not token:
        raise ErroEscritaGlobal(
            "Sua sessão expirou. Entre novamente para enviar o reporte.", 401
        )

    try:
        resposta = requests.post(
            f"{_SUPABASE_URL.rstrip('/')}/functions/v1/secure-global-write",
            json={"operation": operacao, **campos},
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": _ANON_KEY,
                "Content-Type": "application/json",
            },
            timeout=_TIMEOUT_SEGUNDOS,
        )
    except requests.RequestException as exc:
        raise ErroEscritaGlobal(
            "Não foi possível conectar ao serviço de feedback. Tente novamente.",
            503,
        ) from exc

    if resposta.status_code == 200:
        return

    corpo: dict[str, Any] = {}
    try:
        json_resposta = resposta.json()
        if isinstance(json_resposta, dict):
            corpo = json_resposta
    except ValueError:
        pass

    codigo = str(corpo.get("code") or "")
    if codigo == "rate_limited" or resposta.status_code == 429:
        retry_after = corpo.get("retry_after_seconds")
        if not isinstance(retry_after, (int, float)):
            try:
                retry_after = int(resposta.headers.get("Retry-After", "60"))
            except (TypeError, ValueError):
                retry_after = 60
        minutos = max(1, (int(retry_after) + 59) // 60)
        raise ErroEscritaGlobal(
            f"Você atingiu o limite de envios. Tente novamente em {minutos} min.",
            429,
        )

    mensagem, status = _MENSAGENS_ERRO.get(
        codigo,
        ("Não foi possível salvar o feedback no momento.", 502),
    )
    raise ErroEscritaGlobal(mensagem, status)
