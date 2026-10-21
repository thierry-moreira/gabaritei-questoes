import os
from openai import OpenAI
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

openai_key = os.getenv("OPENAI_API_KEY")
MODELO_GPT = "gpt-5.4-mini"
TEMPERATURE_GPT = 0.3
client_gpt = None

if openai_key:
    try:
        client_gpt = OpenAI(api_key=openai_key)
        print(f"✅ Site: OpenAI Ativa (Modelo: {MODELO_GPT})")
    except Exception as e:
        print(f"❌ Erro ao configurar OpenAI para o site: {e}")

MODELO_EXTRACAO = "gpt-5.4-nano" 
client_extracao = None

if client_gpt:
    client_extracao = client_gpt
    print(f"✅ Extração: OpenAI Ativa (Modelo: {MODELO_EXTRACAO})")
else:
    print(f"❌ Extração: Erro ao configurar modelo remoto. Verifique a OPENAI_API_KEY.")