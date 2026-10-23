import os
import random
from flask import Blueprint, render_template, request, redirect, flash, make_response
from flask_login import current_user
try:
    from weasyprint import HTML
except (ImportError, OSError):
    HTML = None

from banco_dados_aluno import supabase
from extensoes import limiter
from utils import safe_execute, aluno_required

simulado_bp = Blueprint('simulado', __name__)

@simulado_bp.route('/aluno/simulados')
@limiter.exempt
@aluno_required
def painel_simulados():
    res_publicos = safe_execute(
        supabase.table("simulados").select("*, usuarios(username)").eq("eh_privado", False).order("criado_em", desc=True)
    )
    simulados_publicos = res_publicos.data or []

    res_privados = safe_execute(
        supabase.table("simulados").select("*").eq("id_criador", current_user.id).eq("eh_privado", True).order("criado_em", desc=True)
    )
    simulados_privados = res_privados.data or []

    materias = safe_execute(supabase.table("materias").select("*").order("nome_materia")).data or []
    escolaridades = safe_execute(supabase.table("niveis_escolaridade").select("*").order("id_nivel")).data or []

    bancas = safe_execute(supabase.table("bancas").select("*").order("nome_banca")).data or []
    
    orgaos = safe_execute(supabase.table("orgaos").select("*").order("nome_orgao")).data or []
    cargos = safe_execute(supabase.table("cargos").select("*").order("nome_cargo")).data or []
    for o in orgaos:
        o['cargos'] = [c for c in cargos if c.get('id_orgao') == o['id_orgao']] # type: ignore
        
    anos_disponiveis = [str(a) for a in range(2026, 1999, -1)]

    return render_template('simulados/index.html', 
                           publicos=simulados_publicos, 
                           privados=simulados_privados,
                           materias=materias,
                           escolaridades=escolaridades,
                           bancas=bancas,
                           orgaos=orgaos,
                           anos=anos_disponiveis)

@simulado_bp.route('/aluno/simulados/gerar', methods=['POST'])
@limiter.exempt
@aluno_required
def gerar_simulado():
    titulo = request.form.get('titulo')
    privacidade = request.form.get('privacidade')
    id_nivel = request.form.get('id_nivel')
    
    eh_privado = True if privacidade == 'privado' else False

    f_bancas = request.form.getlist('bancas[]')
    f_orgaos = request.form.getlist('orgaos[]')
    f_cargos = request.form.getlist('cargos[]')
    f_anos = request.form.getlist('anos[]')
    f_tipos = request.form.getlist('tipos_questao[]')

    materias = request.form.getlist('materias[]')
    topicos = request.form.getlist('topicos[]') 
    quantidades = request.form.getlist('quantidades[]')
    id_simulado = None

    try:
        res_simulado = safe_execute(
            supabase.table('simulados').insert({
                'id_criador': current_user.id,
                'titulo': titulo,
                'eh_privado': eh_privado
            })
        )
        id_simulado = res_simulado.data[0]['id'] # type: ignore

        questoes_selecionadas = []
        
        for mat, top_str, qtd in zip(materias, topicos, quantidades):
            qtd = int(qtd)
            if qtd <= 0: continue

            query = supabase.table('view_questoes_completa').select('id_questao')
            
            if mat:
                query = query.eq('id_materia', mat)
            
            if id_nivel: query = query.eq('id_nivel', id_nivel)
            if f_bancas: query = query.in_('id_banca', f_bancas)
            if f_orgaos: query = query.in_('id_orgao', f_orgaos)
            if f_cargos: query = query.in_('id_cargo', f_cargos)
            if f_anos: query = query.in_('ano', f_anos)
            if f_tipos: query = query.in_('tipo_questao', f_tipos)
            
            if top_str:
                ids_topicos = top_str.split(',')
                query = query.in_('id_topico', ids_topicos)
                
            res_questoes = safe_execute(query.limit(500))
            pool_questoes = res_questoes.data or []

            if len(pool_questoes) > qtd:
                sorteadas = random.sample(pool_questoes, qtd)
            else:
                sorteadas = pool_questoes

            for q in sorteadas:
                questoes_selecionadas.append({
                    'id_simulado': id_simulado,
                    'id_questao': q['id_questao'] # type: ignore
                })

        if questoes_selecionadas:
            safe_execute(supabase.table('simulados_questoes').insert(questoes_selecionadas))
            flash(f"Simulado '{titulo}' gerado com sucesso! {len(questoes_selecionadas)} questões.", "success")
        else:
            safe_execute(supabase.table('simulados').delete().eq('id', id_simulado))
            flash("Não encontramos questões suficientes com esses filtros.", "warning")

    except Exception as e:
        print(f"❌ Erro ao gerar simulado: {e}")
        try:
            if id_simulado is not None:
                safe_execute(supabase.table('simulados').delete().eq('id', id_simulado))
        except Exception:
            pass
            
        flash("Erro ao gerar o simulado. Tente novamente.", "danger")

    return redirect('/aluno/simulados')

@simulado_bp.route('/aluno/simulados/fazer/<id_simulado>')
@limiter.exempt
@aluno_required
def fazer_simulado(id_simulado):
    res_simulado = safe_execute(
        supabase.table('simulados').select('*').eq('id', id_simulado).single()
    )
    simulado = res_simulado.data

    if not simulado:
        flash("Simulado não encontrado.", "danger")
        return redirect('/aluno/simulados')

    if simulado.get('eh_privado') and simulado.get('id_criador') != current_user.id:
        flash("Você não tem permissão para acessar este simulado.", "danger")
        return redirect('/aluno/simulados')

    res_sq = safe_execute(
        supabase.table('simulados_questoes').select('id_questao').eq('id_simulado', id_simulado)
    )
    ids_questoes = [q['id_questao'] for q in (res_sq.data or [])] # type: ignore

    if not ids_questoes:
        flash("Este simulado está vazio.", "warning")
        return redirect('/aluno/simulados')

    res_questoes = safe_execute(
        supabase.table('view_questoes_completa').select('*').in_('id_questao', ids_questoes)
    )
    questoes = res_questoes.data or []

    res_alts = safe_execute(
        supabase.table('alternativas_questao').select('*').in_('id_questao', ids_questoes)
    )
    todas_alternativas = res_alts.data or []

    alts_por_questao = {}
    for alt in todas_alternativas:
        qid = alt['id_questao'] # type: ignore
        if qid not in alts_por_questao:
            alts_por_questao[qid] = []
        alts_por_questao[qid].append(alt)

    for q in questoes:
        lista_alts = alts_por_questao.get(q['id_questao'], []) # type: ignore
        q['alternativas_questao'] = sorted(lista_alts, key=lambda x: x.get('letra', '')) # type: ignore

    random.shuffle(questoes)

    return render_template('simulados/fazer.html', simulado=simulado, questoes=questoes)

@simulado_bp.route('/aluno/simulados/corrigir/<id_simulado>', methods=['POST'])
@limiter.exempt
@aluno_required
def corrigir_simulado(id_simulado):
    try:
        res_simulado = safe_execute(supabase.table('simulados').select('*').eq('id', id_simulado).single())
        simulado = res_simulado.data
        
        res_sq = safe_execute(supabase.table('simulados_questoes').select('id_questao').eq('id_simulado', id_simulado))
        ids_questoes = [q['id_questao'] for q in (res_sq.data or [])] # type: ignore
        
        res_gabaritos = safe_execute(
            supabase.table('alternativas_questao')
            .select('id_questao, letra')
            .eq('is_correct', True)
            .in_('id_questao', ids_questoes)
        )
        
        gabaritos = {item['id_questao']: item['letra'] for item in (res_gabaritos.data or [])} # type: ignore

        acertos = 0
        total = len(ids_questoes)
        detalhes_resultado = []

        for q_id in ids_questoes:
            correta = gabaritos.get(q_id)
            resposta_aluno = request.form.get(f'resp_{q_id}')
            
            eh_correto = (resposta_aluno == correta)
            if eh_correto:
                acertos += 1
                
            detalhes_resultado.append({
                'id_questao': q_id,
                'resposta_aluno': resposta_aluno,
                'resposta_correta': correta,
                'correto': eh_correto
            })

        nota = (acertos / total) * 10 if total > 0 else 0
        
        safe_execute(supabase.table('simulados_resultados').insert({
            'id_simulado': id_simulado,
            'id_usuario': current_user.id,
            'nota': round(nota, 2),
            'respostas_corretas': acertos,
            'total_questoes': total
        }))

        ranking = []
        if not simulado.get('eh_privado'): # type: ignore
            res_ranking = safe_execute(
                supabase.table('simulados_resultados')
                .select('nota, data_conclusao, usuarios(username)')
                .eq('id_simulado', id_simulado)
                .order('nota', desc=True)
                .limit(10)
            )
            ranking = res_ranking.data or []

        return render_template('simulados/resultado.html', 
                               simulado=simulado, 
                               nota=round(nota, 2), 
                               acertos=acertos, 
                               total=total,
                               detalhes=detalhes_resultado,
                               ranking=ranking)

    except Exception as e:
        print(f"Erro na correção: {e}")
        flash("Erro ao corrigir o simulado. Tente novamente.", "danger")
        return redirect('/aluno/simulados')

@simulado_bp.route('/aluno/simulados/excluir/<id_simulado>', methods=['POST'])
@limiter.exempt
@aluno_required
def excluir_simulado(id_simulado):
    try:
        res = safe_execute(supabase.table('simulados').select('id_criador').eq('id', id_simulado).single())
        
        if res.data and res.data.get('id_criador') == current_user.id: # type: ignore
            safe_execute(supabase.table('simulados').delete().eq('id', id_simulado))
            flash("Simulado excluído com sucesso!", "success")
        else:
            flash("Você não tem permissão para excluir este simulado.", "danger")
            
    except Exception as e:
        print(f"Erro ao excluir: {e}")
        flash("Erro ao excluir o simulado.", "danger")
        
    return redirect('/aluno/simulados')

@simulado_bp.route('/aluno/simulados/ranking/<id_simulado>')
@limiter.exempt
@aluno_required
def ver_ranking_simulado(id_simulado):
    try:
        res_simulado = safe_execute(
            supabase.table('simulados').select('titulo, eh_privado').eq('id', id_simulado).single()
        )
        simulado = res_simulado.data

        if not simulado:
            flash("Simulado não encontrado.", "warning")
            return redirect('/aluno/simulados')

        res_ranking = safe_execute(
            supabase.table('simulados_resultados')
            .select('nota, respostas_corretas, total_questoes, data_conclusao, usuarios(username)')
            .eq('id_simulado', id_simulado)
            .order('nota', desc=True)
            .limit(50)
        )
        ranking = res_ranking.data or []

        return render_template('simulados/ranking.html', 
                               simulado=simulado, 
                               ranking=ranking)

    except Exception as e:
        print(f"Erro ao carregar ranking: {e}")
        flash("Erro ao carregar o ranking deste simulado.", "danger")
        return redirect('/aluno/simulados')

@simulado_bp.route('/simulado/<id_simulado>/pdf')
@limiter.exempt 
@aluno_required
def baixar_pdf_simulado(id_simulado):
    try:
        res_simulado = safe_execute(
            supabase.table('simulados').select('*').eq('id', id_simulado).single()
        )
        simulado = res_simulado.data

        if not simulado:
            flash("Simulado não encontrado.", "danger")
            return redirect('/aluno/simulados')

        res_sq = safe_execute(
            supabase.table('simulados_questoes').select('id_questao').eq('id_simulado', id_simulado)
        )
        ids_questoes = [q['id_questao'] for q in (res_sq.data or [])] # type: ignore

        if not ids_questoes:
            flash("Este simulado está vazio.", "warning")
            return redirect('/aluno/simulados')

        res_questoes = safe_execute(
            supabase.table('view_questoes_completa').select('*').in_('id_questao', ids_questoes)
        )
        questoes = res_questoes.data or []

        res_alts = safe_execute(
            supabase.table('alternativas_questao').select('*').in_('id_questao', ids_questoes)
        )
        todas_alternativas = res_alts.data or []

        alts_por_questao = {}
        for alt in todas_alternativas:
            qid = alt['id_questao'] # type: ignore
            if qid not in alts_por_questao:
                alts_por_questao[qid] = []
            alts_por_questao[qid].append(alt)

        for q in questoes:
            lista_alts = alts_por_questao.get(q['id_questao'], []) # type: ignore
            q['alternativas_questao'] = sorted(lista_alts, key=lambda x: x.get('letra', '')) # type: ignore
            
            letra_certa = None
            letra_certa = q.get('gabarito') or q.get('alternativa_correta') or q.get('resposta') or q.get('resposta_correta') # type: ignore
            
            if not letra_certa:
                for a in q['alternativas_questao']: # type: ignore
                    if a.get('is_correta') or a.get('correta') or a.get('certa') or a.get('gabarito'):
                        letra_certa = a.get('letra')
                        break
            
            q['letra_gabarito'] = letra_certa if letra_certa else 'N/A' # type: ignore

        caminho_logo = os.path.abspath('static/logo.webp')
        caminho_css = os.path.abspath('static/css/pdf_style.css')
        
        logo_uri = f"file:///{caminho_logo.replace(os.sep, '/')}"
        css_uri = f"file:///{caminho_css.replace(os.sep, '/')}"

        html_renderizado = render_template(
            'simulados/pdf.html', 
            simulado=simulado, 
            questoes=questoes,
            logo_uri=logo_uri,
            css_uri=css_uri
        )

        if HTML is None:
            raise RuntimeError("WeasyPrint indisponível neste ambiente (bibliotecas GTK/Pango ausentes no Windows).")

        pdf = HTML(string=html_renderizado).write_pdf()

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=Simulado_{id_simulado}.pdf'

        return response

    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {e}")
        flash("Ocorreu um erro ao gerar o PDF. Tente novamente.", "danger")
        return redirect('/aluno/simulados')
