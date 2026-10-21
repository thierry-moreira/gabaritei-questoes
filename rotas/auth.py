import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user

from utils import safe_execute
from banco_dados_aluno import supabase
from modelos import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


def _buscar_aluno_local():
    """Retorna o usuário local (aluno) do desktop, ou None (a tabela usuarios é exclusiva de alunos)."""
    try:
        res = safe_execute(supabase.table("usuarios").select("*").limit(1))
        return res.data[0] if res and res.data else None
    except Exception as e:
        logger.error(f"Erro ao buscar usuário local: {e}", exc_info=True)
        return None


def _entrar(user_data):
    """Efetua o login Flask do usuário local (desktop, sem senha)."""
    login_user(User(
        id=user_data['id'],
        email=user_data.get('email') or '',
        username=user_data.get('username') or 'Estudante',
        role=user_data.get('role') or 'aluno',
    ))
    logger.info(f"LOGIN LOCAL: user_id={user_data['id']}")


@auth_bp.route('/aluno/login')
def login_aluno():
    """Entrada do app desktop: entra direto se o usuário local existe; senão, mostra a tela de criação."""
    if current_user.is_authenticated:
        if current_user.role != 'aluno':
            logout_user()
            flash("A área administrativa roda em aplicativo dedicado (app_admin.py). Aqui é o app do aluno.", "warning")
            return redirect(url_for('auth.login_aluno'))
        return redirect(url_for('aluno.area_do_aluno'))

    usuario = _buscar_aluno_local()
    if usuario:
        _entrar(usuario)
        return redirect(url_for('aluno.area_do_aluno'))

    return render_template('auth/login.html')


@auth_bp.route('/aluno/criar', methods=['POST'])
def criar_usuario():
    """Cria o usuário local do desktop (sem senha) e entra direto."""
    username = (request.form.get('username') or '').strip()
    email = (request.form.get('email') or '').strip()

    if not username:
        flash("Informe como quer ser chamado para criar seu usuário.", "warning")
        return redirect(url_for('auth.login_aluno'))

    existente = _buscar_aluno_local()
    if existente:
        _entrar(existente)
        return redirect(url_for('aluno.area_do_aluno'))

    try:
        dados = {"username": username}
        if email:
            dados["email"] = email

        res = safe_execute(supabase.table("usuarios").insert(dados))
        novo = res.data[0] if res and res.data else None
        if not novo:
            raise RuntimeError("insert sem retorno")

        _entrar(novo)
        flash(f"Bem-vindo, {username}! Seu usuário está pronto.", "success")
        return redirect(url_for('aluno.area_do_aluno'))
    except Exception as e:
        logger.error(f"Erro ao criar usuário local: {e}", exc_info=True)
        flash("Não foi possível criar seu usuário. Tente novamente.", "danger")
        return redirect(url_for('auth.login_aluno'))


@auth_bp.route('/logout')
def logout():
    logout_user()

    keys_to_remove = [k for k in session.keys() if not k.startswith('admin_')]
    for k in keys_to_remove:
        session.pop(k, None)

    return redirect(url_for('aluno.index'))
