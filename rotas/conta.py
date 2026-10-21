from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import current_user, logout_user

from banco_dados_aluno import supabase
from utils import safe_execute, aluno_required
import logging

logger = logging.getLogger(__name__)

conta_bp = Blueprint('conta', __name__)


@conta_bp.route('/aluno/conta/', methods=['GET', 'POST'], strict_slashes=False)
@aluno_required
def ver_configuracoes_conta():
    if request.method == 'POST':
        novo_username = request.form.get('username')
        novo_email = request.form.get('email')

        dados_update = {
            "username": novo_username,
            "email": novo_email or None
        }

        try:
            res = safe_execute(supabase.table("usuarios").update(dados_update).eq("id", current_user.id))

            if res.data:
                flash("Informações atualizadas com sucesso!", "success")
            else:
                flash("Erro ao atualizar dados.", "danger")
        except Exception as e:
            logger.error(f"Erro ao atualizar conta do usuário {current_user.id}: {e}")
            flash("Erro interno no servidor.", "danger")
        
        return redirect('/aluno/conta')

    return render_template('aluno/conta.html')


@conta_bp.route('/aluno/conta/resetar-dados', methods=['POST'])
@aluno_required
def resetar_dados_conta():
    texto_confirmacao = request.form.get('texto_confirmacao_reset', '')

    if texto_confirmacao.strip().upper() != 'RESETAR MEUS DADOS':
        flash("Confirmação incorreta. Digite exatamente 'RESETAR MEUS DADOS' para prosseguir.", "danger")
        return redirect('/aluno/conta')

    user_id = current_user.id

    try:
        safe_execute(supabase.table("usuarios").update({
            "meta_diaria": 0
        }).eq("id", user_id))

        safe_execute(supabase.table("historico_respostas").delete().eq("id_usuario", str(user_id)))

        safe_execute(supabase.table("cadernos").delete().eq("id_usuario", user_id))

        safe_execute(supabase.table("filtros_salvos").delete().eq("id_usuario", user_id))

        safe_execute(supabase.table("flashcard_categorias").delete().eq("id_usuario", user_id))
        safe_execute(supabase.table("flashcards").delete().eq("id_usuario", user_id))

        safe_execute(supabase.table("simulados").delete().eq("id_criador", user_id))

        safe_execute(supabase.table("editais_ciclo").delete().eq("id_usuario", user_id))

        safe_execute(supabase.table("comentarios_questao").delete().eq("id_usuario", user_id))

        flash("✅ Todos os seus dados de estudo foram redefinidos com sucesso! Sua conta está zerada.", "success")
        return redirect('/aluno/conta')

    except Exception as e:
        logger.error(f"Erro ao resetar dados da conta {user_id}: {e}")
        flash("Erro ao tentar resetar os dados. Tente novamente.", "danger")
        return redirect('/aluno/conta')


@conta_bp.route('/aluno/conta/excluir', methods=['POST'])
@aluno_required
def excluir_conta_permanente():
    texto_confirmacao = request.form.get('texto_confirmacao', '')

    if texto_confirmacao.strip().upper() != 'EXCLUIR MINHA CONTA':
        flash("Confirmação incorreta. Digite exatamente 'EXCLUIR MINHA CONTA' para prosseguir.", "danger")
        return redirect('/aluno/conta')

    try:
        
        safe_execute(supabase.table("usuarios").delete().eq("id", current_user.id))
        
        logout_user()
        flash("Sua conta foi excluída permanentemente. Sentiremos sua falta!", "info")
        return redirect('/')
    except Exception as e:
        logger.error(f"Erro ao excluir conta {current_user.id}: {e}")
        flash("Erro ao tentar excluir a conta.", "danger")
        return redirect('/aluno/conta')
