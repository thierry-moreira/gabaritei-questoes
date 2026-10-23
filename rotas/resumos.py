from typing import Any
from datetime import datetime
from flask import Blueprint, render_template, jsonify, abort
from flask_login import login_required, current_user
from banco_dados_aluno import supabase
from utils import safe_execute, aluno_required

resumos_bp = Blueprint('resumos', __name__)

@resumos_bp.route('/aluno/resumos')
@login_required
@aluno_required
def index():
    query = supabase.table('resumos_estudo').select('id_materia, materias(nome_materia)').eq('id_usuario', str(current_user.id))
    res = safe_execute(query)
    
    resumos_lista = res.data if res and res.data else []
    materias_dict: dict[str, dict[str, Any]] = {}
    for r in resumos_lista:
        mid = r['id_materia']
        if mid not in materias_dict:
            materias_dict[mid] = {
                'id': mid,
                'nome': r['materias']['nome_materia'] if r.get('materias') else "Matéria não encontrada",
                'total': 0
            }
        materias_dict[mid]['total'] += 1
        
    return render_template('resumos/index.html', materias=list(materias_dict.values()))

@resumos_bp.route('/aluno/resumos/materia/<int:id_materia>')
@login_required
@aluno_required
def ver_materia(id_materia):
    m_query = supabase.table('materias').select('id_materia, nome_materia').eq('id_materia', id_materia).single()
    m_res = safe_execute(m_query)
    if not m_res or not m_res.data:
        abort(404)
        
    query = supabase.table('resumos_estudo').select('*').eq('id_usuario', str(current_user.id)).eq('id_materia', id_materia).order('criado_em', desc=False)
    res = safe_execute(query)
    resumos = res.data if res and res.data else []
    
    return render_template('resumos/ver_materia.html', resumos=resumos, materia=m_res.data, agora=datetime.now())

@resumos_bp.route('/api/resumos/excluir/<id_resumo>', methods=['POST'])
@login_required
@aluno_required
def excluir(id_resumo):
    query = supabase.table('resumos_estudo').delete().eq('id_resumo', id_resumo).eq('id_usuario', str(current_user.id))
    res = safe_execute(query)
    if res:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Erro ao excluir resumo'})

@resumos_bp.route('/api/resumos/excluir-materia/<int:id_materia>', methods=['POST'])
@login_required
@aluno_required
def excluir_caderno(id_materia):
    query = supabase.table('resumos_estudo').delete().eq('id_materia', id_materia).eq('id_usuario', str(current_user.id))
    res = safe_execute(query)
    if res:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Erro ao excluir caderno'})
