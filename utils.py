import os
import re
import time
import logging
import socket
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import redirect, url_for, flash, request, session
from flask_login import current_user
from typing import Any
from postgrest import CountMethod
from banco_dados_aluno import supabase

logger = logging.getLogger(__name__)

def safe_execute(query_func: Any) -> Any:
    for tentativa in range(3):
        try:
            return query_func.execute()
        except Exception as e:
            if tentativa < 2:
                logger.warning(f"⚠️ Erro na consulta Supabase (Tentativa {tentativa+1}): {e}. Tentando novamente...")
                time.sleep(0.5)
            else:
                logger.error(f"❌ Erro persistente na consulta Supabase após 3 tentativas: {e}")
                raise e

def pegar_ip_real():
    return request.remote_addr

def get_base_url():
    # Aplicação local/desktop: usa a origem da própria requisição (http)
    return request.host_url.rstrip('/')

_bot_cache: dict[str, tuple[bool, float]] = {}

def verificar_bot_real(ip, user_agent):
    if not user_agent:
        return False
        
    ua = user_agent.lower()
    is_google = "googlebot" in ua
    is_bing = "bingbot" in ua
    
    if not (is_google or is_bing):
        return False

    cache = _bot_cache
    agora = time.time()
    
    if ip in cache:
        res, exp = cache[ip]
        if agora < exp:
            return res

    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        
        is_authentic = False
        if is_google and (hostname.endswith(".googlebot.com") or hostname.endswith(".google.com")):
            is_authentic = True
        elif is_bing and hostname.endswith(".search.msn.com"):
            is_authentic = True
            
        if not is_authentic:
            cache[ip] = (False, agora + 3600)
            return False
            
        ip_confirmado = socket.gethostbyname(hostname)
        if ip_confirmado == ip:
            cache[ip] = (True, agora + 86400)
            return True
            
    except (socket.herror, socket.gaierror, Exception) as e:
        logger.warning(f"Falha na verificação de bot para IP {ip}: {e}")
        
    cache[ip] = (False, agora + 3600)
    return False

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

def premium_required(f):
    # Alias para aluno_required - todo usuário autenticado tem acesso premium
    return aluno_required(f)

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

def registrar_log_admin(id_admin, username_admin, tabela, acao, registro_id=None, detalhes=None):
    """Auditoria do painel administrativo: registra em logs_admin QUEM fez a
    alteração (id + username), em QUAL tabela, o TIPO (INSERT/UPDATE/DELETE),
    o registro afetado e QUANDO (data + hora com timezone, via DEFAULT NOW()).
    Falha silenciosa: a auditoria nunca pode derrubar a operação principal."""
    try:
        from banco_dados import supabase
        safe_execute(supabase.table("logs_admin").insert({
            "id_admin": id_admin,
            "username_admin": username_admin or "desconhecido",
            "tabela": tabela,
            "acao": acao,
            "registro_id": registro_id,
            "detalhes": detalhes or {}
        }))
    except Exception as e:
        logging.getLogger(__name__).warning(
            f"Falha ao registrar log de auditoria ({tabela}/{acao}): {e}"
        )
