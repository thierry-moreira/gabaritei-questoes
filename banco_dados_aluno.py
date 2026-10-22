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


# ---------------------------------------------------------------------------
# E-MAILS DO AUTH → PÁGINA PÚBLICA (GitHub Pages)
# ---------------------------------------------------------------------------
# O app é local (127.0.0.1), então o link dos e-mails do Supabase Auth
# (confirmação de cadastro e recuperação de senha) não pode apontar para o
# Site URL local. O clique confirma a conta no servidor do Supabase e
# redireciona para esta página pública, que informa o aluno (e, no caso de
# recuperação de senha, permite definir a nova senha direto nela).
# Fonte da página: site/ do repo — publicada em https://...github.io (ver
# site/README.md). A URL também deve estar na allow list "Redirect URLs"
# do dashboard do Auth (Authentication > URL Configuration).
URL_POS_EMAIL = "https://thierry-moreira.github.io/gabaritei-questoes/"


# ---------------------------------------------------------------------------
# AUTH COM SENHA (Supabase Auth) — identidade real por usuário
# ---------------------------------------------------------------------------
# O client é ÚNICO e a identidade muda com o login: o SDK encadeia o
# access_token nas queries postgrest automaticamente (on_auth_state_change
# atualiza options.headers), preservando os headers custom (x-app-token).
# O processo Flask do app desktop atende UM usuário por vez; a identidade
# troca no login/logout.
#
# RLS: as policies de escrita exigem (eh_app_aluno() AND dono via auth.uid()),
# migration auth_usuario_e_policies. Leitura de dados de estudo continua livre.

def entrar_com_senha(email: str, senha: str):
    """Login email+senha. A partir daqui TODAS as queries saem com o JWT do
    usuário (auth.uid() passa a identificar o dono nas policies)."""
    return supabase.auth.sign_in_with_password({"email": email, "password": senha})


def criar_conta_auth(email: str, senha: str):
    """Cria a conta no Supabase Auth. Com 'Confirm email' desligado devolve
    sessão pronta; ligado, devolve user pendente de confirmação (sem sessão).
    O e-mail de confirmação redireciona para a página pública (URL_POS_EMAIL)."""
    return supabase.auth.sign_up({
        "email": email,
        "password": senha,
        "options": {"email_redirect_to": URL_POS_EMAIL},
    })


def restaurar_sessao(refresh_token: str):
    """Restaura a sessão de um boot anterior a partir do refresh token
    (guardado na sessão Flask). Reautentica o client global."""
    return supabase.auth.refresh_session(refresh_token)


def definir_sessao(access_token: str, refresh_token: str):
    """Reaplica tokens (relogin silencioso sem nova ida ao servidor Auth)."""
    return supabase.auth.set_session(access_token, refresh_token)


def sessao_atual():
    """Sessão Auth corrente (None se o client está anônimo/expirado)."""
    return supabase.auth.get_session()


def sair_auth():
    """Limpa a identidade do client global (volta a anônimo)."""
    supabase.auth.sign_out()


def pedir_reset_senha(email: str):
    """Dispara o e-mail de recuperação do Supabase (requer SMTP configurado
    no dashboard do projeto). O link redireciona para a página pública
    (URL_POS_EMAIL), onde o aluno define a nova senha."""
    supabase.auth.reset_password_for_email(
        email, options={"redirect_to": URL_POS_EMAIL})