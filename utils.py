import re
import time
import logging
import unicodedata
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import redirect, url_for, session
from flask_login import current_user
from typing import Any
from banco_dados_aluno import supabase

logger = logging.getLogger(__name__)

# Códigos de erro determinísticos (Postgres/PostgREST) nos quais retentar é
# inútil — a falha não depende de timing: 23505 unique violation, 23503 FK,
# 23502 not null, 23514 check, 42501 RLS, 42703 coluna inexistente,
# 22P02 tipo inválido. Falhas de rede/timeout/5xx continuam com retry.
ERROS_SEM_RETRY = ("23505", "23503", "23502", "23514", "42501", "42703", "22P02")

# Limites/formatos compartilhados por cadastro, conta e comentários.
# A mesma regra existe como CHECK no banco (migration comentarios_username_xss).
USERNAME_MIN = 2
USERNAME_MAX = 30
TEXTO_COMENTARIO_MAX = 1000

# Allowlist: letras (inclusive acentuadas), números, espaço, ponto, hífen e
# sublinhado. `\w` em str já cobre Unicode; nada de <, >, aspas, &, barras etc.
_RE_USERNAME = re.compile(r"^[\w .-]+$", re.UNICODE)
_RE_CONTROLE = re.compile(r"[\x00-\x1f\x7f]")

_TERMOS_IMPROPRIOS = (
    "porra", "caralho", "merda", "puta", "putaria", "putinha", "putas", "putona",
    "viado", "gay", "gays", "idiota",
    "imbecil", "burro", "jumento", "desgraça", "vagabundo", "vaca",
    "vacas", "safado", "canalha", "corno", "arrombado", "foda", "filho da puta",
    # Grafias comuns e erros de digitação de "foder".
    "foder", "fuder", "fode", "fude", "fodr", "fudr", "fueder", "fudder",
)
# Exigem limite também no fim para não bloquear palavras legítimas que os
# contenham como prefixo (por exemplo, "computador", "disputa" e "vacância").
_TERMOS_IMPROPRIOS_EXATOS = {"gay", "puta", "vaca"}
_MAPA_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t"})


def _normalizar_texto_improprio(texto):
    texto = unicodedata.normalize("NFKD", texto.casefold())
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return texto.translate(_MAPA_LEET)


def _compilar_padrao_improprio(termo):
    termo_normalizado = _normalizar_texto_improprio(termo)
    caracteres = [caractere for caractere in termo_normalizado if caractere.isalnum()]
    if not caracteres:
        return None

    corpo = r"[\W_]{0,3}".join(re.escape(caractere) + "+" for caractere in caracteres)
    termo_compacto = "".join(caracteres)
    exige_fim_de_palavra = (
        termo_compacto in _TERMOS_IMPROPRIOS_EXATOS or " " in termo_normalizado
    )
    limite_final = r"(?!\w)" if exige_fim_de_palavra else ""
    return re.compile(r"(?<!\w)" + corpo + limite_final)


_PADROES_IMPROPRIOS = tuple(
    padrao
    for padrao in map(_compilar_padrao_improprio, _TERMOS_IMPROPRIOS)
    if padrao is not None
)


def validar_username(username):
    """Normaliza e valida o nome de usuário exibido na comunidade.

    Retorna ``(username_normalizado, "")`` quando válido ou
    ``(None, mensagem)`` quando inválido. A normalização remove espaços nas
    pontas e colapsa espaços internos, preservando o nome exibido.
    """
    if not isinstance(username, str):
        return None, "Nome de usuário inválido."

    username = re.sub(r"\s+", " ", username).strip()
    if not (USERNAME_MIN <= len(username) <= USERNAME_MAX):
        return None, (
            f"O nome de usuário deve ter entre {USERNAME_MIN} e "
            f"{USERNAME_MAX} caracteres."
        )
    if not _RE_USERNAME.fullmatch(username):
        return None, (
            "O nome de usuário pode conter apenas letras, números, espaços, "
            "ponto, hífen e sublinhado."
        )
    return username, ""


def validar_texto_comentario(texto):
    """Valida o texto do comentário antes de gravar.

    O texto é armazenado como veio (sem escapar entidades): a defesa contra
    XSS é feita na saída, com ``textContent`` no JS. Aqui rejeitamos apenas
    payloads inválidos (tipo errado, vazio, longo demais ou com caracteres de
    controle), mantendo o conteúdo legítimo intacto.
    """
    if not isinstance(texto, str):
        return None, "Comentário inválido."

    texto = texto.strip()
    if not texto:
        return None, "Escreva um comentário antes de enviar."
    if len(texto) > TEXTO_COMENTARIO_MAX:
        return None, (
            f"O comentário deve ter no máximo {TEXTO_COMENTARIO_MAX} caracteres."
        )
    if _RE_CONTROLE.search(texto):
        return None, "O comentário contém caracteres inválidos."
    return texto, ""


def _erro_deterministico(e: Exception) -> bool:
    """True quando retentar não muda o resultado (constraint/RLS/typo de query)."""
    texto = str(e)
    return any(codigo in texto for codigo in ERROS_SEM_RETRY)


def safe_execute(query_func: Any) -> Any:
    for tentativa in range(3):
        try:
            return query_func.execute()
        except Exception as e:
            if _erro_deterministico(e):
                logger.error(f"❌ Erro determinístico na consulta Supabase (sem retry): {e}")
                raise e
            if tentativa < 2:
                logger.warning(f"⚠️ Erro na consulta Supabase (Tentativa {tentativa+1}): {e}. Tentando novamente...")
                time.sleep(0.5)
            else:
                logger.error(f"❌ Erro persistente na consulta Supabase após 3 tentativas: {e}")
                raise e

def verificar_texto_improprio(texto):
    if not texto:
        return True, ""

    texto_normalizado = _normalizar_texto_improprio(texto)
    if any(padrao.search(texto_normalizado) for padrao in _PADROES_IMPROPRIOS):
        return False, "Seu comentário contém termos que violam as diretrizes da comunidade. Por favor, mantenha o respeito."

    # Moderação sem IA (decisão de produto): a blocklist local acima é a
    # primeira barreira; a segunda é a denúncia humana (🚩 em cada comentário,
    # endpoint /api/comentarios/<id>/reportar → triagem no painel do admin).
    return True, ""

def aluno_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'aluno':
            logger.warning(f"🔍 aluno_required BLOCKED: is_authenticated={current_user.is_authenticated}, role={getattr(current_user, 'role', 'N/A')}, session={dict(session)}")
            return redirect(url_for('auth.login_aluno'))
        return f(*args, **kwargs)
    return decorated_function

def calcular_ofensiva_usuario(user_id):
    try:
        user_id_str = str(user_id)
        query = supabase.table("historico_respostas")\
            .select("criado_em")\
            .eq("id_usuario", user_id_str)\
            .order("criado_em", desc=True)

        res = safe_execute(query)

        if not res.data:
            return 0

        datas_resolvidas = []
        for r in res.data:
            try:
                data_str = r['criado_em'][:19].replace('T', ' ')
                dt_utc = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
                dt_brasilia = dt_utc - timedelta(hours=3)
                datas_resolvidas.append(dt_brasilia.date())
            except:
                continue 

        datas_resolvidas = sorted(list(set(datas_resolvidas)), reverse=True)

        hoje_brasilia = (datetime.now(timezone.utc) - timedelta(hours=3)).date()
        ofensiva = 0
        data_esperada = hoje_brasilia

        for d in datas_resolvidas:
            if d == data_esperada:
                ofensiva += 1
                data_esperada -= timedelta(days=1)
            elif d > data_esperada: 
                continue
            else:
                if ofensiva == 0 and d == hoje_brasilia - timedelta(days=1):
                    ofensiva = 1
                    data_esperada = d - timedelta(days=1)
                    continue
                break
        
        return ofensiva

    except Exception as e:
        print(f"⚠️ Erro no cálculo da ofensiva: {e}")
        return 0

def slugify(text):
    if not text:
        return ""
    import unicodedata
    import re
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text

