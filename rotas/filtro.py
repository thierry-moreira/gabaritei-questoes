import logging
from flask import Blueprint, request, redirect, flash, jsonify
from flask_login import current_user

from banco_dados_aluno import supabase
from extensoes import limiter
from utils import safe_execute, aluno_required

logger = logging.getLogger(__name__)

filtro_bp = Blueprint('filtro', __name__)

@filtro_bp.route('/aluno/salvar_filtro', methods=['POST'])
@limiter.exempt
@aluno_required
def salvar_filtro():
    url_params = request.form.get('url_params', '')

    nome = request.form.get('nome_filtro')

    try:
        safe_execute(
            supabase.table("filtros_salvos").insert({
                "id_usuario": current_user.id,
                "nome_filtro": nome,
                "url_params": url_params
            })
        )
        flash("Filtro salvo com sucesso!", "success")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar filtro para o usuário {current_user.id}: {e}")
        flash("Erro ao salvar filtro.", "danger")
        
    return redirect(f"/aluno/questoes?{url_params}")

@filtro_bp.route('/aluno/excluir_filtro/<filtro_id>', methods=['POST'])
@limiter.exempt
@aluno_required
def excluir_filtro(filtro_id):
    try:
        safe_execute(
            supabase.table("filtros_salvos")
            .delete()
            .eq("id", filtro_id)
            .eq("id_usuario", current_user.id)
        )
        return jsonify({"status": "sucesso", "mensagem": "Filtro excluído!"})
    except Exception as e:
        logger.error(f"❌ Erro ao excluir filtro {filtro_id}: {e}")
        return jsonify({"status": "erro", "mensagem": "Falha ao excluir."}), 500
