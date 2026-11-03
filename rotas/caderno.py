from flask import Blueprint, render_template, redirect, url_for, abort, jsonify, request
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
    # O caderno é dado privado: filtra pelo dono na origem. O RLS owner-only
    # também bloqueia, mas o filtro explícito evita depender só dele. "não
    # existe" e "não é seu" devolvem o mesmo 404 (não revela a existência).
    try:
        res_caderno = safe_execute(
            supabase.table("cadernos")
            .select("nome_caderno")
            .eq("id_caderno", id_caderno)
            .eq("id_usuario", current_user.id)
            .limit(1)
        )
    except Exception as e:
        print(f"❌ ERRO CRÍTICO NO CADERNO: {str(e)}")
        return redirect(url_for('caderno.meus_cadernos'))

    if not res_caderno or not res_caderno.data:
        abort(404)

    nome_caderno = res_caderno.data[0].get('nome_caderno', "Caderno sem nome")

    try:
        res_ids = safe_execute(
            supabase.table("caderno_questoes")
            .select("id_questao")
            .eq("id_caderno", id_caderno)
            .eq("id_usuario", current_user.id)
        )
        ids_questoes = [item['id_questao'] for item in (res_ids.data or [])] if res_ids else []

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

            # id_usuario é text em historico_respostas (legado); usa o id do
            # usuário autenticado, nunca um valor arbitrário de sessão.
            historico = safe_execute(
                supabase.table('historico_respostas')
                .select('id_questao, is_correct')
                .eq('id_usuario', str(current_user.id))
                .in_('id_questao', ids_questoes)
            )

            # Type narrowing: ensure historico.data is a non-empty list of dicts
            if historico and historico.data and isinstance(historico.data, list) and len(historico.data) > 0:
                historico_list: list[dict[str, Any]] = historico.data  # type: ignore[assignment]
                ids_acertos = [h['id_questao'] for h in historico_list if h['is_correct']]
                ids_erros = [h['id_questao'] for h in historico_list if not h['is_correct']]

        return render_template('questoes/visualizar.html',
                               nome_caderno=nome_caderno,
                               questoes=questoes_lista,
                               id_caderno=id_caderno,
                               ids_acertos=ids_acertos,
                               ids_erros=ids_erros)
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
    dados = request.get_json(silent=True) or {}
    id_caderno = dados.get('id_caderno')
    id_questao = dados.get('id_questao')

    if not id_caderno or id_questao is None:
        return jsonify({"success": False, "error": "Dados incompletos"}), 400

    try:
        id_questao_int = int(id_questao)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Formato do ID da questão inválido."}), 400

    # F-03: id_caderno vem do cliente. Confirma que o caderno pertence ao
    # aluno antes de inserir; 404 não revela a existência de cadernos alheios.
    try:
        res_caderno = safe_execute(
            supabase.table("cadernos")
            .select("id_caderno")
            .eq("id_caderno", id_caderno)
            .eq("id_usuario", current_user.id)
            .limit(1)
        )
    except Exception as e:
        print(f"❌ Erro ao validar caderno {id_caderno}: {e}")
        return jsonify({"success": False, "error": "Erro de conexão ao salvar"}), 500

    if not res_caderno or not res_caderno.data:
        return jsonify({"success": False, "error": "Caderno não encontrado"}), 404

    query = supabase.table("caderno_questoes").insert({
        "id_caderno": id_caderno,
        "id_questao": id_questao_int,
        "id_usuario": current_user.id
    })
    try:
        safe_execute(query)
        return jsonify({"success": True})
    except Exception as e:
        msg = str(e).lower()
        if "duplicate key" in msg:
            return jsonify({"success": False, "error": "Esta questão já está neste caderno"}), 400
        # Backstop da FK composta: caderno removido/trocado de dono entre a
        # checagem e o INSERT, ou chamada fora do app.
        if "caderno_questoes_caderno_dono_fkey" in msg or "caderno_questoes_id_caderno_fkey" in msg:
            return jsonify({"success": False, "error": "Caderno não encontrado"}), 404
        if "caderno_questoes_id_questao_fkey" in msg:
            return jsonify({"success": False, "error": "Questão não encontrada"}), 400
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
