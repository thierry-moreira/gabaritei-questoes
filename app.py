from datetime import datetime
import os
import sys
import time

from typing import Any
from postgrest import CountMethod

# Garante que sys.stdout e sys.stderr nao quebrem com emojis no console Cp1252 do Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        getattr(sys.stdout, 'reconfigure')(errors='backslashreplace')
    if hasattr(sys.stderr, 'reconfigure'):
        getattr(sys.stderr, 'reconfigure')(errors='backslashreplace')
except:
    pass
import gzip
from io import BytesIO
from flask import Flask, render_template, flash, session, request
from dotenv import load_dotenv
from flask_login import current_user
import logging
import mimetypes
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_compress import Compress

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')

from banco_dados_aluno import supabase
from modelos import User
from extensoes import login_manager, limiter, csrf
from utils import calcular_ofensiva_usuario

from rotas.auth import auth_bp
from rotas.api import api_bp
from rotas.aluno import aluno_bp
from rotas.simulado import simulado_bp
from rotas.edital import edital_bp
from rotas.conta import conta_bp
from rotas.caderno import caderno_bp
from rotas.filtro import filtro_bp
from rotas.questao import questao_bp
from rotas.flashcards import flashcards_bp
from rotas.resumos import resumos_bp

load_dotenv()

app = Flask(__name__)
# Desativa o Rate Limiter em testes unitarios para evitar erros 429 involuntarios
import sys
if any('unittest' in arg for arg in sys.argv) or app.config.get('TESTING') or app.testing:
    app.config['RATELIMIT_ENABLED'] = False

Compress(app)

_secret_key = os.getenv("FLASK_SECRET_KEY")
if not _secret_key:
    import sys
    logger.error("❌ ERRO CRÍTICO DE SEGURANÇA: FLASK_SECRET_KEY não configurada no arquivo .env!")
    sys.exit(1)

app.config['SECRET_KEY'] = _secret_key

# Aplicação local/desktop: sempre HTTP, sem exigência de HTTPS ou cookie seguro
app.config.update(
    SESSION_COOKIE_NAME='__session',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,    # HTTP local: cookie SEM a flag Secure
    SESSION_COOKIE_SAMESITE='Lax',  # 'Lax' funciona via HTTP ('None' exigiria HTTPS)
    SESSION_COOKIE_DOMAIN=None,
    PREFERRED_URL_SCHEME='http',    # URLs externas/e-mails gerados como http://
)

@app.after_request
def compress(response):
    accept_encoding = request.headers.get('Accept-Encoding', '')
    if 'gzip' not in accept_encoding.lower():
        return response
        
    if response.status_code < 200 or response.status_code >= 300:
        return response
    if 'Content-Encoding' in response.headers:
        return response

    content_type = response.headers.get('Content-Type', '')
    # Não comprimir SSE (Server-Sent Events) — quebraria o streaming
    if 'text/event-stream' in content_type:
        return response
    if not any(t in content_type for t in ['text/html', 'text/css', 'application/javascript', 'application/json']):
        return response

    response.direct_passthrough = False
    gzip_buffer = BytesIO()
    gzip_file = gzip.GzipFile(mode='wb', fileobj=gzip_buffer)
    gzip_file.write(response.get_data())
    gzip_file.close()
    
    response.set_data(gzip_buffer.getvalue())
    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Content-Length'] = len(response.get_data())
    
    return response

app.register_blueprint(auth_bp)
app.register_blueprint(aluno_bp)
app.register_blueprint(api_bp)
app.register_blueprint(simulado_bp)
app.register_blueprint(edital_bp)
app.register_blueprint(conta_bp)
app.register_blueprint(caderno_bp)
app.register_blueprint(filtro_bp)
app.register_blueprint(questao_bp)
app.register_blueprint(flashcards_bp)
app.register_blueprint(resumos_bp)

proxies_confiaveis = int(os.getenv("TRUSTED_PROXIES", "0"))
if proxies_confiaveis > 0:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxies_confiaveis, x_proto=1, x_host=1, x_prefix=1)
    logger.info(f"🛡️ ProxyFix ATIVADO (Confiando em {proxies_confiaveis} proxy/proxies).")
else:
    logger.warning("⚠️ ProxyFix DESATIVADO. Configure 'TRUSTED_PROXIES=1' no .env para habilitar o Rate Limiter.")

login_manager.init_app(app)
limiter.init_app(app)
csrf.init_app(app) 

from flask_talisman import Talisman

csp = {
    'default-src': ['\'self\''],
    'script-src': [
        '\'self\'',
        '\'unsafe-inline\'',
        'https://cdn.jsdelivr.net',
        'https://cdn.ckeditor.com',
    ],
    'style-src': [
        '\'self\'',
        '\'unsafe-inline\'',
        'https://cdn.jsdelivr.net',
        'https://fonts.googleapis.com',
    ],
    'img-src': [
        '\'self\'',
        'data:',
        'blob:',
        'https://cdn.jsdelivr.net',
        'https://illustrations.popsy.co',
        'https://*.supabase.co',
    ],
    'font-src': ['\'self\'', 'data:', 'https://cdn.jsdelivr.net', 'https://fonts.gstatic.com'],
    'connect-src': [
        '\'self\'',
        'https://api.openai.com',
        'https://cdn.jsdelivr.net',
        'https://*.supabase.co',
        'https://cdn.ckeditor.com',
    ],
    'frame-src': [
        '\'self\'',
    ],
}

talisman = Talisman(
    app, 
    content_security_policy=csp, 
    force_https=False,
    strict_transport_security=False,  # HTTP local: sem header HSTS (resquício web-era)
    session_cookie_secure=False,  # Impede a lib de forçar a flag Secure (HTTP local)
    session_cookie_samesite='Lax',
    permissions_policy={
        "browsing-topics": [],
    }
)

# --- Auth com senha (Supabase Auth): mantém o client autenticado -------------
# O client global perde a sessão a cada boot do processo; o refresh token vive
# na sessão Flask (cookie persistente). Aqui o reaplicamos no primeiro request
# de quem já está logado no Flask-Login.
from banco_dados_aluno import sessao_atual as _sessao_auth_atual, restaurar_sessao as _restaurar_sessao_auth

@app.before_request
def _garantir_sessao_auth():
    if current_user.is_authenticated:
        try:
            if _sessao_auth_atual() is None:
                rt = session.get('auth_refresh_token')
                if rt:
                    _restaurar_sessao_auth(rt)
        except Exception:
            pass

@app.errorhandler(429)
def ratelimit_handler(e):
    flash("Muitas tentativas de acesso. Por segurança, aguarde 1 minuto.", "danger")
    return render_template('auth/login.html'), 429

from utils import slugify
app.jinja_env.filters['slugify'] = slugify

@app.context_processor
def inject_global_data():
    if not current_user.is_authenticated:
        return dict(global_streak=0)

    total_flashcards = 0
    try:
        res_f = supabase.table("flashcards").select("id_flashcard", count=CountMethod.exact).eq("id_usuario", current_user.id).lte("proxima_revisao", datetime.now().isoformat()).execute()
        total_flashcards = res_f.count if res_f and res_f.count is not None else 0
    except:
        pass

    return dict(
        global_streak=calcular_ofensiva_usuario(current_user.id),
        global_flashcards_revisar=total_flashcards,
    )

@login_manager.user_loader
def load_user(user_id):
    if app.config.get('TESTING') or app.testing:
        return User(
            id=user_id,
            email="teste@gabaritei.com.br",
            username="Usuario Teste",
            role="aluno",
        )

    for tentativa in range(3):
        try: 
            # Converter user_id para int se for numérico (evita mismatch de tipo no Supabase)
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                user_id_int = user_id
            
            logger.info(f"🔍 load_user: user_id={user_id}, user_id_int={user_id_int}, tentativa={tentativa+1}")
            
            res = supabase.table("usuarios").select("*").eq("id", user_id_int).execute()
            logger.info(f"🔍 load_user: query result count={len(res.data) if res.data else 0}")
            
            if res.data and isinstance(res.data[0], dict):
                u: dict[str, Any] = res.data[0]
                
                logger.info(f"🔍 load_user: Returning User id={u['id']} (aluno)")
                return User(
                    id=u['id'],
                    email=u['email'],
                    username=u.get('username') or u.get('nome') or 'Estudante',
                    role='aluno',
                    tema=u.get('tema', 'light')
                ) 
            logger.warning(f"🔍 load_user: No user data found for id={user_id_int}")
            return None
        except Exception as e: 
            logger.error(f"⚠️ Erro no load_user (tentativa {tentativa+1}): {e}")
            time.sleep(0.5) 
    return None


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=(os.getenv('FLASK_DEBUG', 'false').lower() == 'true'))
