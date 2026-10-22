from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from banco_dados_aluno import supabase
from extensoes import limiter
from utils import safe_execute, aluno_required
from flask_login import current_user
from datetime import datetime, timedelta
from postgrest import CountMethod
from typing import Any

flashcards_bp = Blueprint('flashcards', __name__)

@flashcards_bp.route('/aluno/flashcards')
@limiter.exempt
@aluno_required
def index():
    try:
        query_cat = supabase.table("flashcard_categorias")\
            .select("*, materias(nome_materia)")\
            .eq("id_usuario", current_user.id)
        res_cat = safe_execute(query_cat)
        categorias = res_cat.data if res_cat and res_cat.data else []

        agora = datetime.now().isoformat()
        query_revisar = supabase.table("flashcards")\
            .select("id_flashcard", count=CountMethod.exact)\
            .eq("id_usuario", current_user.id)\
            .lte("proxima_revisao", agora)
        res_revisar = safe_execute(query_revisar)
        total_revisar = res_revisar.count if res_revisar else 0

        return render_template('flashcards/index.html', 
                               categorias=categorias, 
                               total_revisar=total_revisar)
    except Exception as e:
        print(f"Erro no dashboard de flashcards: {e}")
        return render_template('flashcards/index.html', categorias=[], total_revisar=0)

@flashcards_bp.route('/aluno/flashcards/categoria/<id_categoria>')
@limiter.exempt
@aluno_required
def gerenciar_categoria(id_categoria):
    try:
        query_cat = supabase.table("flashcard_categorias").select("*").eq("id_categoria", id_categoria).eq("id_usuario", current_user.id).single()
        res_cat = safe_execute(query_cat)
        categoria = res_cat.data

        if not categoria:
            return redirect(url_for('flashcards.index'))

        query_cards = supabase.table("flashcards")\
            .select("*")\
            .eq("id_categoria", id_categoria)\
            .eq("id_usuario", current_user.id)\
            .order("criado_em", desc=True)
        res_cards = safe_execute(query_cards)
        cards = res_cards.data if res_cards and res_cards.data else []

        return render_template('flashcards/gerenciar.html', categoria=categoria, cards=cards)
    except Exception as e:
        return redirect(url_for('flashcards.index'))

@flashcards_bp.route('/aluno/flashcards/estudar/<id_categoria>')
@limiter.exempt
@aluno_required
def estudar(id_categoria):
    try:
        agora = datetime.now().isoformat()
        query = supabase.table("flashcards")\
            .select("*")\
            .eq("id_usuario", current_user.id)\
            .lte("proxima_revisao", agora)
        
        if id_categoria != 'todos':
            query = query.eq("id_categoria", id_categoria)
            
        res = safe_execute(query)
        cards = res.data if res and res.data else []
        
        return render_template('flashcards/estudar.html', cards=cards, id_categoria=id_categoria)
    except Exception as e:
        return redirect(url_for('flashcards.index'))

@flashcards_bp.route('/api/flashcards/categoria/nova', methods=['POST'])
@aluno_required
def criar_categoria():
    dados = request.get_json()
    nome = dados.get('nome')
    if not nome: return jsonify({"success": False, "error": "Nome obrigatório"}), 400
    
    try:
        user_id_str = str(current_user.id)
        query = supabase.table("flashcard_categorias").insert({
            "id_usuario": user_id_str,
            "nome_categoria": nome
        })
        res = safe_execute(query)
        
        if not res.data:
            return jsonify({"success": False, "error": "Falha ao inserir categoria"}), 500
            
        return jsonify({"success": True, "categoria": res.data[0]})
    except Exception as e:
        print(f"❌ ERRO AO CRIAR CATEGORIA: {e}")
        return jsonify({"success": False, "error": "Erro interno ao criar categoria."}), 500

@flashcards_bp.route('/api/flashcards/criar', methods=['POST'])
@aluno_required
def criar_card():
    dados = request.get_json()
    id_cat = dados.get('id_categoria')
    frente = dados.get('frente')
    verso = dados.get('verso')
    
    if not frente or not verso: 
        return jsonify({"success": False, "error": "Campos obrigatórios"}), 400
    
    try:
        user_id_str = str(current_user.id)
        query = supabase.table("flashcards").insert({
            "id_usuario": user_id_str,
            "id_categoria": id_cat,
            "frente": frente,
            "verso": verso,
            "proxima_revisao": datetime.now().isoformat()
        })
        res = safe_execute(query)
        return jsonify({"success": True, "card": res.data[0]})
    except Exception as e:
        print(f"❌ ERRO AO CRIAR CARD: {e}")
        return jsonify({"success": False, "error": "Erro interno ao criar flashcard."}), 500

@flashcards_bp.route('/api/flashcards/revisar', methods=['POST'])
@aluno_required
def revisar_card():
    dados = request.get_json()
    id_card = dados.get('id_flashcard')
    qualidade = int(dados.get('qualidade', 0))

    try:
        res_card = supabase.table("flashcards").select("*").eq("id_flashcard", id_card).eq("id_usuario", current_user.id).single().execute()
        card = res_card.data

        if not card:
            return jsonify({"success": False, "error": "Flashcard não encontrado."}), 404
        
        # Type narrowing: ensure card is a dict with numeric fields
        card_dict: dict[str, Any] = card  # type: ignore[assignment]
        
        intervalo = card_dict.get('intervalo', 0)
        facilidade = card_dict.get('facilidade', 2.5)
        
        # Ensure numeric types
        intervalo = float(intervalo) if intervalo is not None else 0.0
        facilidade = float(facilidade) if facilidade is not None else 2.5
        
        if qualidade == 0:
            novo_intervalo = 0
            nova_facilidade = max(1.3, facilidade - 0.2)
        elif qualidade == 1:
            novo_intervalo = max(1, int(intervalo * 1.2))
            nova_facilidade = max(1.3, facilidade - 0.15)
        elif qualidade == 2:
            if intervalo == 0: novo_intervalo = 1
            elif intervalo == 1: novo_intervalo = 4
            else: novo_intervalo = int(intervalo * facilidade)
            nova_facilidade = facilidade
        else:
            if intervalo <= 1: novo_intervalo = 7
            else: novo_intervalo = int(intervalo * facilidade * 1.3)
            nova_facilidade = min(2.5, facilidade + 0.15)

        proxima = datetime.now() + timedelta(days=novo_intervalo)
        
        supabase.table("flashcards").update({
            "intervalo": novo_intervalo,
            "facilidade": nova_facilidade,
            "proxima_revisao": proxima.isoformat()
        }).eq("id_flashcard", id_card).eq("id_usuario", current_user.id).execute()
        
        return jsonify({"success": True, "novo_intervalo": novo_intervalo})
    except Exception as e:
        print(f"❌ ERRO AO REVISAR CARD: {e}")
        return jsonify({"success": False, "error": "Erro interno ao revisar flashcard."}), 500

@flashcards_bp.route('/api/flashcards/excluir/<id_card>', methods=['POST'])
@aluno_required
def excluir_card(id_card):
    try:
        supabase.table("flashcards").delete().eq("id_flashcard", id_card).eq("id_usuario", current_user.id).execute()
        return jsonify({"success": True})
    except Exception as e:
        print(f"❌ ERRO AO EXCLUIR CARD: {e}")
        return jsonify({"success": False, "error": "Erro interno ao excluir flashcard."}), 500

@flashcards_bp.route('/api/flashcards/categoria/excluir/<id_categoria>', methods=['POST'])
@aluno_required
def excluir_categoria(id_categoria):
    try:
        user_id_str = str(current_user.id)
        supabase.table("flashcard_categorias")\
            .delete()\
            .eq("id_categoria", id_categoria)\
            .eq("id_usuario", user_id_str)\
            .execute()
        return jsonify({"success": True})
    except Exception as e:
        print(f"❌ ERRO AO EXCLUIR CATEGORIA: {e}")
        return jsonify({"success": False, "error": "Erro interno ao excluir categoria."}), 500
