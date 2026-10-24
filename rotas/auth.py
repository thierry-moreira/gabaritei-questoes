import logging
import secrets

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user

from utils import safe_execute
from banco_dados_aluno import (
    supabase, entrar_com_senha, criar_conta_auth, restaurar_sessao,
    sessao_atual, sair_auth, pedir_reset_senha,
)
from modelos import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

MIN_SENHA = 8


def _linha_do_usuario_auth():
    """Linha de public.usuarios do usuário logado no Auth (None se não há)."""
    s = sessao_atual()
    if not s or not s.user:
        return None
    try:
        res = safe_execute(supabase.table("usuarios").select("*").eq("auth_id", s.user.id).limit(1))
        return res.data[0] if res and res.data else None
    except Exception as e:
        logger.error(f"Erro ao buscar perfil do usuário Auth: {e}", exc_info=True)
        return None


def _entrar_flask(linha):
    """Efetua o login Flask-Login e guarda o refresh token (lembrar no boot)."""
    login_user(User(
        id=linha['id'],
        email=linha.get('email') or '',
        username=linha.get('username') or 'Estudante',
        role='aluno',
    ))
    s = sessao_atual()
    if s and s.refresh_token:
        session['auth_refresh_token'] = s.refresh_token
    # Sessão eterna do desktop: SEM session.permanent o Flask emite um
    # "session cookie" (sem data de expiração) e o Chromium do Electron o
    # DESCARTA ao fechar o app — o aluno teria que logar a cada abertura.
    # Com permanent=True o cookie ganha Expires (permanent_session_lifetime,
    # definido no app.py) e sobrevive indefinidamente.
    session.permanent = True
    logger.info(f"LOGIN: user_id={linha['id']}")


def _relinkar_perfil_legado():
    """Adota o perfil legado (auth_id NULL) de mesmo e-mail — 1º login pós-Auth.

    Alunos do sistema antigo (web/passwordless) ficaram sem auth_id. A policy
    `relink_perfil_legado` (migration relink_perfil_legado_usuarios) só deixa
    o UPDATE passar quando o e-mail CONFIRMADO do JWT bate com o e-mail da
    linha — o filtro de e-mail é feito pelo próprio RLS (case-insensitive);
    aqui só restringimos a linhas ainda sem vínculo (auth_id IS NULL).
    """
    s = sessao_atual()
    if not s or not s.user:
        return None
    try:
        res = safe_execute(
            supabase.table("usuarios")
            .update({"auth_id": s.user.id})
            .is_("auth_id", "null")
        )
        return res.data[0] if res and res.data else None
    except Exception as e:
        logger.warning(f"Re-link de perfil legado falhou para {s.user.email}: {e}")
        return None


def _criar_perfil(username, email):
    """Garante a linha `usuarios` da conta Auth logada.

    Ordem: (1) perfil legado sem auth_id de mesmo e-mail → re-link (evita
    duplicar o aluno e colidir nas uniques de username/e-mail — causa do
    500 no login após a migração para Supabase Auth); (2) cria linha nova
    — se o username colidir (ex.: dois e-mails com o mesmo prefixo), tenta
    com sufixo _hex (padrão do cadastro antigo do site).
    """
    s = sessao_atual()
    if not s or not s.user:
        return None

    linha = _relinkar_perfil_legado()
    if linha:
        return linha

    base = (username or 'Estudante').strip() or 'Estudante'
    for sufixo in ("", "_" + secrets.token_hex(2)):
        try:
            res = safe_execute(supabase.table("usuarios").insert({
                "auth_id": s.user.id,
                "username": base + sufixo,
                "email": email,
            }))
            return res.data[0] if res and res.data else None
        except Exception as e:
            if "23505" in str(e) and not sufixo:
                logger.warning(f"Username '{base}' já existe; tentando com sufixo.")
                continue
            logger.error(f"Criação de perfil falhou para {s.user.email}: {e}", exc_info=True)
            return None
    return None


@auth_bp.route('/aluno/login')
def login_aluno():
    """Entrada do app: restaura o login anterior (refresh) ou mostra a tela."""
    if current_user.is_authenticated:
        return redirect(url_for('aluno.area_do_aluno'))

    rt = session.get('auth_refresh_token')
    if rt:
        try:
            restaurar_sessao(rt)
        except Exception:
            session.pop('auth_refresh_token', None)
            try:
                sair_auth()
            except Exception:
                pass
        else:
            linha = _linha_do_usuario_auth()
            if linha:
                _entrar_flask(linha)
                return redirect(url_for('aluno.area_do_aluno'))

    return render_template('auth/login.html')


@auth_bp.route('/aluno/entrar', methods=['POST'])
def entrar():
    """Login com e-mail + senha (Supabase Auth)."""
    email = (request.form.get('email') or '').strip().lower()
    senha = request.form.get('senha') or ''

    if not email or not senha:
        flash("Informe e-mail e senha.", "warning")
        return redirect(url_for('auth.login_aluno'))

    try:
        entrar_com_senha(email, senha)
    except Exception as e:
        logger.warning(f"Login negado para {email}: {e}")
        flash("E-mail ou senha incorretos.", "danger")
        return redirect(url_for('auth.login_aluno'))

    linha = _linha_do_usuario_auth()
    if not linha:
        # Conta Auth ok, mas sem perfil (ex.: perfil apagado) — recria
        linha = _criar_perfil((email or 'Estudante').split('@')[0], email)
    if not linha:
        try:
            sair_auth()
        except Exception:
            pass
        flash("Não foi possível carregar seu perfil. Tente novamente.", "danger")
        return redirect(url_for('auth.login_aluno'))

    _entrar_flask(linha)
    return redirect(url_for('aluno.area_do_aluno'))


@auth_bp.route('/aluno/criar', methods=['POST'])
def criar_usuario():
    """Cadastro: cria a conta Auth (e-mail + senha) e o perfil do aluno."""
    username = (request.form.get('username') or '').strip()
    email = (request.form.get('email') or '').strip().lower()
    senha = request.form.get('senha') or ''
    confirmar_senha = request.form.get('confirmar_senha') or ''

    if not username or not email or not senha:
        flash("Preencha nome, e-mail e senha para criar sua conta.", "warning")
        return redirect(url_for('auth.login_aluno'))
    if len(senha) < MIN_SENHA:
        flash(f"A senha precisa ter no mínimo {MIN_SENHA} caracteres.", "warning")
        return redirect(url_for('auth.login_aluno'))
    if senha != confirmar_senha:
        flash("As senhas não conferem. Digite a mesma senha nos dois campos.", "warning")
        return redirect(url_for('auth.login_aluno'))

    try:
        criar_conta_auth(email, senha)
    except Exception as e:
        msg = str(e)
        logger.warning(f"Cadastro falhou para {email}: {msg}")
        if "already" in msg.lower() or "registered" in msg.lower() or "exists" in msg.lower():
            flash("Este e-mail já tem conta. Faça login ou recupere a senha.", "warning")
        else:
            flash("Não foi possível criar sua conta. Tente novamente.", "danger")
        return redirect(url_for('auth.login_aluno'))

    s = sessao_atual()
    if not s or not s.user:
        # "Confirm email" ligado no Auth: conta criada, aguardando confirmação
        flash("Conta criada! Confirme seu e-mail pelo link enviado e depois faça login.", "info")
        return redirect(url_for('auth.login_aluno'))

    linha = _criar_perfil(username, email)
    if not linha:
        flash("Conta criada, mas o perfil falhou. Faça login com e-mail e senha para completar.", "warning")
        return redirect(url_for('auth.login_aluno'))

    _entrar_flask(linha)
    flash(f"Bem-vindo, {username}! Sua conta está pronta.", "success")
    return redirect(url_for('aluno.area_do_aluno'))


@auth_bp.route('/aluno/esqueci', methods=['POST'])
def esqueci_senha():
    """Dispara o e-mail de recuperação de senha (Supabase Auth + SMTP)."""
    email = (request.form.get('email') or '').strip().lower()
    if not email:
        flash("Informe seu e-mail para recuperar a senha.", "warning")
        return redirect(url_for('auth.login_aluno'))
    try:
        pedir_reset_senha(email)
        flash("Se este e-mail tiver conta, enviamos um link para redefinir a senha. Confira sua caixa de entrada (e o spam).", "info")
    except Exception as e:
        logger.error(f"Reset de senha falhou para {email}: {e}", exc_info=True)
        flash("Não foi possível enviar o e-mail de recuperação agora. Tente novamente mais tarde.", "danger")
    return redirect(url_for('auth.login_aluno'))


@auth_bp.route('/logout')
def logout():
    try:
        sair_auth()
    except Exception:
        pass
    logout_user()

    keys_to_remove = [k for k in session.keys() if not k.startswith('admin_')]
    for k in keys_to_remove:
        session.pop(k, None)

    return redirect(url_for('auth.login_aluno'))