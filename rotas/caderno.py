from flask import Blueprint, render_template, redirect, url_for, session, jsonify, request
from flask_login import current_user
from typing import Any

from banco_dados_aluno import supabase
from extensoes import limiter
from utils import safe_execute, aluno_required

caderno_bp = Blueprint('caderno', __name__)


@caderno_bp.route('/aluno/meus_cadernos')
@limiter.exempt
@aluno_required
def meus_cadernos():
    query = supabase.table("cadernos").select("*").eq("id_usuario", current_user.id)
    try:
        res = safe_execute(query)
        cadernos = res.data if res.data else []
        return render_template('questoes/cadernos.html', cadernos=cadernos)
    except Exception as e:
        print(f"⚠️ Erro ao carregar página de cadernos: {e}")
        return render_template('questoes/cadernos.html', cadernos=[], erro="Falha na conexão com o banco.")


@caderno_bp.route('/aluno/caderno/<id_caderno>')
@limiter.exempt
@aluno_required
def visualizar_caderno(id_caderno):
    try:
        id_usuario = session.get('id_usuario')
        
        query_nome = supabase.table("cadernos").select("nome_caderno").eq("id_caderno", id_caderno).single()
        res_caderno = safe_execute(query_nome)
        nome_caderno = res_caderno.data.get('nome_caderno', "Caderno sem nome") if res_caderno and res_caderno.data else "Caderno sem nome"
        
        query_ids = supabase.table("caderno_questoes").select("id_questao").eq("id_caderno", id_caderno)
        res_ids = safe_execute(query_ids)
        ids_questoes = [item['id_questao'] for item in res_ids.data] if res_ids and res_ids.data else []
        
        questoes_lista = []
        ids_acertos = []
        ids_erros = []
        
        if ids_questoes:
            query_detalhes = supabase.table("view_questoes_completa")\
                .select("*, alternativas_questao(*)")\
                .in_("id_questao", ids_questoes)
            res_detalhes = safe_execute(query_detalhes)
            if res_detalhes and res_detalhes.data:
                questoes_lista = res_detalhes.data
                
            historico = supabase.table('historico_respostas')\
                .select('id_questao, is_correct')\
                .eq('id_usuario', id_usuario)\
                .in_('id_questao', ids_questoes)\
                .execute()
                
            # Type narrowing: ensure historico.data is a non-empty list of dicts
            if historico.data and isinstance(historico.data, list) and len(historico.data) > 0:
                historico_list: list[dict[str, Any]] = historico.data  # type: ignore[assignment]
                ids_acertos = [h['id_questao'] for h in historico_list if h['is_correct']]
                ids_erros = [h['id_questao'] for h in historico_list if not h['is_correct']]
                
        return render_template('questoes/visualizar.html', 
                               nome_caderno=nome_caderno,
                               questoes=questoes_lista,
                               id_caderno=id_caderno,
                               ids_acertos=ids_acertos,
                               ids_erros=ids_erros,
                                is_premium=True)
    except Exception as e:
        print(f"❌ ERRO CRÍTICO NO CADERNO: {str(e)}")
        return redirect(url_for('caderno.meus_cadernos'))


@caderno_bp.route('/api/cadernos', methods=['GET'])
@limiter.exempt
@aluno_required
def listar_cadernos():
    query = supabase.table("cadernos").select("*").eq("id_usuario", current_user.id)
    try:
        res = safe_execute(query)
        return jsonify(res.data if res.data else [])
    except Exception as e:
        print(f"⚠️ Erro ao listar cadernos: {e}")
        return jsonify([])


@caderno_bp.route('/api/cadernos/novo', methods=['POST'])
@limiter.exempt
@aluno_required
def criar_caderno():
    nome = request.get_json().get('nome')
    if not nome:
        return jsonify({"error": "Nome do caderno é obrigatório"}), 400
        
    query = supabase.table("cadernos").insert({
        "id_usuario": current_user.id, 
        "nome_caderno": nome
    })
    try:
        res = safe_execute(query)
        if res.data:
            return jsonify({"success": True, "caderno": res.data[0]})
        return jsonify({"success": False, "error": "Falha ao criar caderno"}), 500
    except Exception as e:
        print(f"❌ Erro ao criar caderno: {e}")
        return jsonify({"error": "Falha ao criar caderno"}), 500


@caderno_bp.route('/api/cadernos/salvar', methods=['POST'])
@limiter.exempt
@aluno_required
def salvar_na_pasta():
    dados = request.get_json()
    id_caderno = dados.get('id_caderno')
    id_questao = dados.get('id_questao')
    
    query = supabase.table("caderno_questoes").insert({
        "id_caderno": id_caderno,
        "id_questao": id_questao,
        "id_usuario": current_user.id
    })
    try:
        safe_execute(query)
        return jsonify({"success": True})
    except Exception as e:
        if "duplicate key" in str(e).lower():
            return jsonify({"success": False, "error": "Esta questão já está neste caderno"}), 400
        print(f"❌ Erro ao salvar questão no caderno: {e}")
        return jsonify({"success": False, "error": "Erro de conexão ao salvar"}), 500


@caderno_bp.route('/api/cadernos/excluir/<id_caderno>', methods=['POST'])
@limiter.exempt
@aluno_required
def excluir_caderno(id_caderno):
    query_delete = supabase.table("cadernos")\
        .delete()\
        .eq("id_caderno", id_caderno)\
        .eq("id_usuario", current_user.id)
    try:
        safe_execute(query_delete)
        return jsonify({"success": True})
    except Exception as e:
        print(f"❌ Erro ao excluir caderno {id_caderno}: {e}")
        return jsonify({"success": False, "error": "Não foi possível excluir o caderno. Tente novamente."}), 500


@caderno_bp.route('/api/cadernos/remover_questao', methods=['POST'])
@limiter.exempt
@aluno_required
def remover_questao_caderno():
    if current_user.role != 'aluno':
        return jsonify({"success": False, "error": "Acesso negado"}), 403
        
    dados = request.get_json()
    id_caderno = dados.get('id_caderno')
    id_questao = dados.get('id_questao')
    
    if not id_caderno or not id_questao:
        return jsonify({"success": False, "error": "Dados incompletos"}), 400
        
    try:
        id_questao_int = int(id_questao)
        user_id = current_user.id
        
        query_delete = (
            supabase.table("caderno_questoes")
            .delete()
            .eq("id_caderno", id_caderno)
            .eq("id_questao", id_questao_int)
            .eq("id_usuario", user_id)
        )
        safe_execute(query_delete)
        return jsonify({"success": True})
    except ValueError:
        return jsonify({"success": False, "error": "Formato do ID da questão inválido."}), 400
    except Exception as e:
        print(f"❌ Erro REAL ao remover questão do caderno: {e}")
        return jsonify({"success": False, "error": "Erro ao remover questão do caderno."}), 500
