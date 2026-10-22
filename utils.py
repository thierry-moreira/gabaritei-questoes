import re
import time
import logging
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

    BLOCKLIST = [
        "porra", "caralho", "merda", "puta", "viado", "gay", "idiota", 
        "imbecil", "burro", "jumento", "desgraça", "vagabundo", "vaca", 
        "safado", "canalha", "corno", "arrombado", "foda", "filho da puta"
    ]
    
    texto_limpo = texto.lower()
    texto_normalizado = re.sub(r'[\.\-\_]', '', texto_limpo)

    for palavra in BLOCKLIST:
        if palavra in texto_limpo or palavra in texto_normalizado:
            return False, "Seu comentário contém termos que violam nossas diretrizes de comunidade. Por favor, mantenha o respeito."

    try:
        from extensoes import client_gpt
        if client_gpt:
            response = client_gpt.moderations.create(input=texto)
            if response.results[0].flagged:
                return False, "Sua mensagem foi identificada como inadequada pela nossa moderação automática."
    except Exception as e:
        print(f"⚠️ Falha na Moderação via API (seguindo com filtro local): {e}")

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

