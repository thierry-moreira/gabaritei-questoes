"""Recuperação de legislação curada para grounding da IA (RAG leve).

O app do aluno NÃO ingere legislação: o corpus curado vive no Supabase
(tabela `legislacao_artigos`), alimentado pelo painel administrativo
(service_role) — ver docs/migrations/legislacao_busca.sql.

Princípio central: FAIL-OPEN. A recuperação é um enriquecimento opcional
do prompt: qualquer falha (RPC inexistente, rede, migration ainda não
aplicada) devolve lista vazia e a geração da explicação segue exatamente
como antes. O RAG jamais pode ser o motivo de uma explicação não nascer.

Retrieval LEXICAL/ESTRUTURADO (Postgres FTS em português + filtros da
taxonomia id_materia/id_topico), não vetorial:
- legislação é altamente lexical ("art. 117 Lei 8.112", "CF art. 37");
- o FTS roda no mesmo PostgREST já usado pelo app, é gratuito e não
  depende de embeddings — a camada BYOK não tem API de embeddings
  compatível entre OpenAI, Gemini e Anthropic.
"""
import html
import logging
import re
from typing import Any

from banco_dados_aluno import supabase

logger = logging.getLogger(__name__)

LIMITE_PADRAO = 5          # máx. de trechos injetados no prompt
MAX_TEXTO_TRECHO = 1500    # corte por trecho (orçamento de contexto)
MAX_TEXTO_CONSULTA = 1500  # corte do enunciado usado na busca
MINIMO_CONSULTA = 15       # enunciado curto demais não discrimina


def limpar_html(texto: Any) -> str:
    """Remove tags/entidades do enunciado e normaliza espaços (FTS limpa)."""
    if not texto:
        return ""
    sem_tags = re.sub(r"<[^>]+>", " ", str(texto))
    sem_entidades = html.unescape(sem_tags)
    return re.sub(r"\s+", " ", sem_entidades).strip()


def _cortar(texto: str, limite: int) -> str:
    """Trunca em `limite` caracteres preferindo quebra de palavra."""
    if len(texto) <= limite:
        return texto
    corte = texto[:limite].rsplit(" ", 1)[0]
    return (corte or texto[:limite]).rstrip() + " …"


def recuperar_legislacao(
    id_materia: Any,
    id_topico: Any,
    enunciado: Any,
    limite: int = LIMITE_PADRAO,
) -> list[dict[str, Any]]:
    """Busca trechos de legislação curada para a questão (fail-open).

    Retorna lista de dicts {id, referencia, texto, vigencia_de, vigencia_ate}
    — vazia quando não há contexto, quando a consulta é inconclusiva ou
    quando a RPC `buscar_legislacao` ainda não existe no Supabase.
    """
    texto = _cortar(limpar_html(enunciado), MAX_TEXTO_CONSULTA)
    if len(texto) < MINIMO_CONSULTA:
        return []

    params: dict[str, Any] = {
        "p_texto": texto,
        "p_limite": max(1, min(limite, LIMITE_PADRAO)),
    }
    if id_materia:
        params["p_id_materia"] = id_materia
    if id_topico:
        params["p_id_topico"] = id_topico

    try:
        # Tentativa única, SEM safe_execute de propósito: se a migration da
        # RPC ainda não foi aplicada (PGRST202 função inexistente), 3
        # retries de 0,5 s em toda geração virariam latência inútil — o
        # contrato aqui é fail-open, não resiliência.
        res = supabase.rpc("buscar_legislacao", params).execute()
    except Exception as e:
        logger.warning(f"⚠️ Contexto legislativo indisponível (fail-open): {e}")
        return []

    trechos: list[dict[str, Any]] = []
    for linha in (res.data or []):
        if not isinstance(linha, dict) or not linha.get("texto"):
            continue
        trechos.append({
            "id": linha.get("id"),
            "referencia": str(linha.get("referencia") or "Legislação").strip(),
            "texto": _cortar(str(linha["texto"]).strip(), MAX_TEXTO_TRECHO),
            "vigencia_de": linha.get("vigencia_de"),
            "vigencia_ate": linha.get("vigencia_ate"),
        })
    return trechos


def _formatar_vigencia(trecho: dict[str, Any]) -> str:
    """Anotação de vigência — 'VIGÊNCIA ENCERRADA' sinaliza redação antiga."""
    de = trecho.get("vigencia_de")
    ate = trecho.get("vigencia_ate")
    if ate:
        return f" — VIGÊNCIA ENCERRADA em {ate} (redação histórica)"
    if de:
        return f" — vigente desde {de}"
    return ""


def montar_bloco_contexto(trechos: list[dict[str, Any]]) -> str:
    """Monta o bloco de texto dos trechos para injetar no prompt do usuário."""
    if not trechos:
        return ""
    partes = []
    for i, t in enumerate(trechos, 1):
        cabecalho = f"[{i}] {t.get('referencia', 'Legislação')}{_formatar_vigencia(t)}"
        partes.append(f"{cabecalho}\n{t.get('texto', '')}")
    return "\n\n".join(partes)


def montar_evidencia(trechos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """IDs/referências dos trechos usados — gravados junto do cache global
    (`explicacoes_ia.contexto_legislacao`) para auditoria e revalidação."""
    return [
        {"id": t.get("id"), "referencia": t.get("referencia")}
        for t in trechos
        if t.get("referencia")
    ]
