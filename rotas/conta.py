from flask import Blueprint, render_template, request, redirect, flash, url_for, jsonify
from flask_login import current_user, logout_user

from banco_dados_aluno import supabase
from utils import safe_execute, aluno_required
import logging

# BYOK (Bring Your Own Key): a chave de IA do aluno fica SOMENTE no banco
# local (banco_local.py — SQLite + DPAPI). Nada vai para o Supabase.
from provedores_ia import PROVEDORES, testar_chave
from banco_local import ler_config_ia, salvar_config_ia, remover_config_ia, mascarar_chave

logger = logging.getLogger(__name__)

conta_bp = Blueprint('conta', __name__)


def _status_ia_do_aluno():
    """Snapshot seguro (com máscara da chave) da configuração de IA do aluno."""
    config = ler_config_ia(current_user.id)
    if not config or config.get("provedor") not in PROVEDORES:
        return None
    return {
        "provedor": config["provedor"],
        "nome_provedor": PROVEDORES[config["provedor"]]["nome"],
        "modelo": config["modelo"],
        "mascara": mascarar_chave(config["chave"]),
    }


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

    return render_template(
        'aluno/conta.html',
        ia_status=_status_ia_do_aluno(),
        provedores_ia=PROVEDORES,
    )


# ----------------------------------------------------------------------------
# Inteligência Artificial — BYOK: o aluno usa a PRÓPRIA chave de API
# ----------------------------------------------------------------------------
@conta_bp.route('/api/ia/config', methods=['POST'])
@aluno_required
def salvar_config_ia_conta():
    """Valida (ping gratuito) e grava a chave localmente — nunca no Supabase."""
    dados = request.get_json() or {}
    provedor = (dados.get('provedor') or '').strip()
    modelo = (dados.get('modelo') or '').strip()
    chave = (dados.get('chave') or '').strip()

    if provedor not in PROVEDORES:
        return jsonify({"success": False, "error": "Provedor não suportado."}), 400
    if not chave or len(chave) < 20:
        return jsonify({"success": False, "error": "Chave de API inválida (muito curta)."}), 400

    if not modelo:
        modelo = PROVEDORES[provedor]["modelo_padrao"]
    elif len(modelo) > 80:
        return jsonify({"success": False, "error": "Nome de modelo inválido."}), 400

    try:
        ok, motivo = testar_chave(provedor, chave, modelo)
    except Exception as e:
        logger.error(f"Erro ao validar chave de IA do usuário {current_user.id}: {e}")
        return jsonify({"success": False, "error": "Não foi possível validar a chave agora. Tente novamente."}), 502

    if not ok:
        return jsonify({"success": False, "error": motivo}), 400

    salvar_config_ia(current_user.id, provedor, modelo, chave)
    logger.info(
        f"🔑 Config de IA salva LOCALMENTE (provedor={provedor}, modelo={modelo}) "
        f"para o usuário {current_user.id}"
    )
    return jsonify({"success": True, "status": _status_ia_do_aluno()})


@conta_bp.route('/api/ia/config/remover', methods=['POST'])
@aluno_required
def remover_config_ia_conta():
    """Apaga a chave de IA deste dispositivo (LGPD — direito ao esquecimento)."""
    removido = remover_config_ia(current_user.id)
    return jsonify({"success": True, "removido": removido})


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

        # Progresso de editais (tabelas com dono — migration auth_usuario_e_policies)
        safe_execute(supabase.table("editais_materias").delete().eq("id_usuario", user_id))
        safe_execute(supabase.table("editais_topicos").delete().eq("id_usuario", user_id))
        safe_execute(supabase.table("editais_progresso").delete().eq("id_usuario", user_id))

        safe_execute(supabase.table("comentarios_questao").delete().eq("id_usuario", user_id))

        # Denúncias feitas pelo aluno (reports_comentarios — migration reports_comentarios_p1)
        safe_execute(supabase.table("reports_comentarios").delete().eq("id_usuario", user_id))

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
        
        # LGPD: apaga as denúncias do aluno e a chave de IA LOCAL deste dispositivo
        safe_execute(supabase.table("reports_comentarios").delete().eq("id_usuario", str(current_user.id)))
        safe_execute(supabase.table("usuarios").delete().eq("id", current_user.id))
        try:
            remover_config_ia(current_user.id)
        except Exception as e:
            logger.error(f"Não foi possível apagar a chave de IA local na exclusão da conta: {e}")
        
        logout_user()
        flash("Sua conta foi excluída permanentemente. Sentiremos sua falta!", "info")
        return redirect('/')
    except Exception as e:
        logger.error(f"Erro ao excluir conta {current_user.id}: {e}")
        flash("Erro ao tentar excluir a conta.", "danger")
        return redirect('/aluno/conta')
