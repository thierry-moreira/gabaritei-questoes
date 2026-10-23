from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

limiter = Limiter(
    key_func=get_remote_address, 
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

csrf = CSRFProtect()

login_manager = LoginManager()
login_manager.login_view = 'auth.login_aluno' # type: ignore
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"

# IA (BYOK): não existe mais cliente global de IA neste app — cada aluno usa a
# PRÓPRIA chave de API (OpenAI, Google Gemini ou Anthropic), configurada em
# Configurações da conta e guardada apenas localmente (DPAPI). As chamadas
# passam pela camada provedores_ia.py; prompts e parâmetros calibrados vivem
# nas rotas (rotas/questao.py), sem alteração.