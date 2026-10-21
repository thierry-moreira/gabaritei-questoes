from flask import Blueprint, jsonify, request

from banco_dados_aluno import supabase
from utils import safe_execute, aluno_required
from extensoes import limiter

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/cargos/<int:id_orgao>')
@limiter.limit("60 per minute")
def get_cargos_por_orgao(id_orgao):
    try:
        res = supabase.table("cargos")\
            .select("id_cargo, nome_cargo")\
            .eq("id_orgao", id_orgao)\
            .order("nome_cargo")\
            .execute()
        return jsonify(res.data)
    except Exception as e:
        print(f"⚠️ Erro ao carregar cargos: {e}")
        return jsonify({"error": "Erro ao carregar cargos."}), 500


@api_bp.route('/api/get_assuntos_cascata', methods=['POST'])
@limiter.exempt
@aluno_required
def get_assuntos_cascata():
    dados = request.get_json()
    ids_materias = dados.get('ids_materias', [])

    if not ids_materias:
        return jsonify([])

    try:
        res_topicos = safe_execute(
            supabase.table("topicos")
            .select("id_topico, nome_topico")
            .in_("id_materia", ids_materias)
            .order("nome_topico")
        )
        topicos = res_topicos.data or []

        if not topicos:
            return jsonify([])

        ids_topicos_encontrados = [t['id_topico'] for t in topicos]

        res_sub = safe_execute(
            supabase.table("subtopicos")
            .select("id_subtopico, nome_subtopico, id_topico")
            .in_("id_topico", ids_topicos_encontrados)
            .order("nome_subtopico")
        )
        subtopicos = res_sub.data or []

        arvore_final = []
        for t in topicos:
            filhos = [
                {
                    "id": s['id_subtopico'],
                    "nome": s['nome_subtopico']
                }
                for s in subtopicos if s['id_topico'] == t['id_topico']
            ]
            
            arvore_final.append({
                "id": t['id_topico'],
                "nome": t['nome_topico'],
                "subtopicos": filhos
            })

        return jsonify(arvore_final)

    except Exception as e:
        print(f"❌ Erro na cascata de assuntos: {e}")
        return jsonify({"error": "Erro ao carregar assuntos."}), 500


@api_bp.route('/api/topicos/<int:id_materia>')
@limiter.limit("60 per minute")
def get_topicos(id_materia):
    try:
        query = supabase.table("topicos").select("*").eq("id_materia", id_materia)
        res = safe_execute(query)
        return jsonify(res.data or [])
    except Exception as e:
        print(f"⚠️ Erro ao carregar tópicos: {e}")
        return jsonify([])


@api_bp.route('/api/subtopicos/<int:id_topico>')
@limiter.limit("60 per minute")
def get_subtopicos(id_topico):
    try:
        query = supabase.table("subtopicos").select("*").eq("id_topico", id_topico)
        res = safe_execute(query)
        return jsonify(res.data or [])
    except Exception as e:
        print(f"⚠️ Erro ao carregar subtópicos: {e}")
        return jsonify([])


@api_bp.route('/api/usuario/preferencias', methods=['POST'])
@aluno_required
def salvar_preferencias():
    from flask_login import current_user
    dados = request.get_json()
    tema = dados.get('tema')
    
    if tema not in ['light', 'dark']:
        return jsonify({"error": "Tema inválido"}), 400
        
    try:
        supabase.table("usuarios")\
            .update({"tema": tema})\
            .eq("id", current_user.id)\
            .execute()
        return jsonify({"success": True})
    except Exception as e:
        print(f"❌ Erro ao salvar tema no banco: {e}")
        return jsonify({"error": "Erro ao salvar preferências."}), 500
