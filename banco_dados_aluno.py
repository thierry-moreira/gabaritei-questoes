import os
from dotenv import load_dotenv
from typing import cast
from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions

# App do ALUNO (futuro Electron distribuído): usa a ANON key — pública por
# definição (vai embarcada no binário) e protegida pelas policies RLS
# (migration rls_policies_aluno). A service_role (SUPABASE_KEY em
# banco_dados.py) é EXCLUSIVA do painel administrativo — jamais embarcar
# no app do aluno. O nome exportado é o mesmo `supabase` de propósito:
# rotas e testes (patches) não mudam.
#
# APP_TOKEN: segredo de app injetado no header x-app-token de TODAS as
# requisições — as policies de ESCRITA do aluno exigem esse header
# (RLS valida via public.eh_app_aluno()). Extraído apenas junto com o
# binário (mesmo nível de esforço da anon key, mas fecha o "curl fácil").
load_dotenv()

url = cast(str, os.environ.get("SUPABASE_URL"))
anon_key = cast(str, os.environ.get("SUPABASE_ANON_KEY"))
app_token = cast(str, os.environ.get("APP_TOKEN"))

if not url or not anon_key:
    raise ValueError("ERRO CRÍTICO: As credenciais do Supabase (SUPABASE_URL/SUPABASE_ANON_KEY) não foram encontradas no .env (app do aluno)")
if not app_token:
    raise ValueError("ERRO CRÍTICO: APP_TOKEN não configurado no .env — as policies de escrita do app do aluno exigem o header x-app-token")

opts = SyncClientOptions(
    postgrest_client_timeout=30,
    headers={"Connection": "close", "x-app-token": app_token} 
)

supabase: Client = create_client(url, anon_key, options=opts)