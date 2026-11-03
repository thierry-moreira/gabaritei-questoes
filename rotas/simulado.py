import random
from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import current_user

from banco_dados_aluno import supabase
from extensoes import limiter
from utils import safe_execute, aluno_required

simulado_bp = Blueprint('simulado', __name__)


def _buscar_simulado(id_simulado):
    """Busca um simulado visível ao usuário atual.

    Primeiro tenta a tabela `simulados` (RLS owner-only: cobre os simulados
    do próprio aluno, inclusive privados). Se não houver linha, cai para a
    view pública, que só expõe simulados com `eh_privado = false` e nunca
    devolve `id_criador`, e-mail ou auth_id. Simulado privado de outro aluno
    não aparece em nenhuma das duas consultas.
    """
    try:
        res = safe_execute(
            supabase.table('simulados').select('*').eq('id', id_simulado).limit(1)
        )
        if res.data:
            return res.data[0]

        res = safe_execute(
            supabase.table('view_simulados_publicos')
            .select('*')
            .eq('id', id_simulado)
            .limit(1)
        )
        if res.data:
            linha = res.data[0]
            return {
                'id': linha['id'],
                'titulo': linha['titulo'],
                'descricao': linha.get('descricao'),
                'eh_privado': False,
                'id_criador': current_user.id if linha.get('eh_meu') else None,
            }
    except Exception as e:
        print(f"❌ Erro ao buscar simulado {id_simulado}: {e}")
    return None


def _simulado_do_usuario_ou_none(id_simulado):
    """Guard único de acesso a simulado: devolve a linha visível ou None.

    Regra aplicada por fazer/corrigir/ranking/PDF antes de qualquer consulta
    de questões, gabarito, resultados ou RPC:

      * simulado inexistente -> None;
      * simulado privado de outro aluno -> None (mesma resposta do inexistente,
        sem revelar que o ID existe);
      * simulado público de qualquer aluno -> permitido;
      * simulado do próprio aluno (público ou privado) -> permitido.

    `_buscar_simulado` já esconde o privado alheio (RLS owner-only + view
    pública), mas a checagem explícita de `eh_privado`/`id_criador` mantém o
    contrato mesmo se a origem da consulta mudar.
    """
    simulado = _buscar_simulado(id_simulado)
    if not simulado:
        return None
    if simulado.get('eh_privado') and simulado.get('id_criador') != current_user.id:
        return None
    return simulado


def _ids_questoes_do_simulado(id_simulado):
    """IDs das questões visíveis: tabela (dono) ou view pública."""
    res = safe_execute(
        supabase.table('simulados_questoes')
        .select('id_questao')
        .eq('id_simulado', id_simulado)
    )
    ids = [q['id_questao'] for q in (res.data or [])]
    if ids:
        return ids

    res = safe_execute(
        supabase.table('view_simulados_questoes_publicas')
        .select('id_questao')
        .eq('id_simulado', id_simulado)
    )
    return [q['id_questao'] for q in (res.data or [])]


def _ranking_simulado(id_simulado):
    """Ranking via RPC segura (público: authenticated; privado: criador)."""
    res = safe_execute(
        supabase.rpc('ranking_simulado', {'p_id_simulado': id_simulado})
    )
    return res.data or []


@simulado_bp.route('/aluno/simulados')
@limiter.exempt
@aluno_required
def painel_simulados():
    # Feed público via view: simulados eh_privado=false de qualquer aluno,
    # com o username do criador e sem id_criador/email (F-01).
    res_publicos = safe_execute(
        supabase.table("view_simulados_publicos").select("*").order("criado_em", desc=True)
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
    simulado = _simulado_do_usuario_ou_none(id_simulado)

    if not simulado:
        # Privado de outro aluno e inexistente recebem a mesma resposta.
        flash("Simulado não encontrado.", "danger")
        return redirect('/aluno/simulados')

    ids_questoes = _ids_questoes_do_simulado(id_simulado)

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
        simulado = _simulado_do_usuario_ou_none(id_simulado)
        if not simulado:
            # Mesma resposta para privado alheio e inexistente: não revela ID.
            flash("Simulado não encontrado.", "danger")
            return redirect('/aluno/simulados')

        ids_questoes = _ids_questoes_do_simulado(id_simulado)

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

        # A RPC libera ranking público para qualquer autenticado e ranking
        # privado apenas para o criador; devolve somente username + métricas.
        ranking = _ranking_simulado(id_simulado)[:10]

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
        # Owner-only: a linha de outro aluno nem aparece aqui. `.limit(1)` em
        # vez de `.single()` evita o erro PGRST116 de "0 linhas" e mantém a
        # resposta igual para "não existe" e "não é seu".
        res = safe_execute(
            supabase.table('simulados').select('id_criador').eq('id', id_simulado).limit(1)
        )

        if res.data and res.data[0].get('id_criador') == current_user.id:
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
        simulado = _simulado_do_usuario_ou_none(id_simulado)

        if not simulado:
            # Não revela se o ID existe: privado de outro aluno e inexistente
            # recebem a mesma resposta.
            flash("Simulado não encontrado.", "warning")
            return redirect('/aluno/simulados')

        ranking = _ranking_simulado(id_simulado)

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
        simulado = _simulado_do_usuario_ou_none(id_simulado)

        if not simulado:
            # Privado de outro aluno e inexistente recebem a mesma resposta.
            flash("Simulado não encontrado.", "danger")
            return redirect('/aluno/simulados')

        ids_questoes = _ids_questoes_do_simulado(id_simulado)

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


        # Prévia navegável com o botão "Imprimir / Salvar PDF" — a mesma
        # experiência dos resumos, unificada para navegador E desktop:
        # imprimirOuPDF() (imprimir_ou_pdf.js) chama electronAPI.printToPDF()
        # no app desktop (o Chromium do Electron não renderiza
        # application/pdf inline) e window.print() no navegador (preview de
        # impressão nativo → "Salvar como PDF"). O @media print da página
        # esconde a barra de ações e expande a folha A4 do caderno.
        return render_template(
            'simulados/pdf_preview.html',
            simulado=simulado,
            questoes=questoes,
            logo_uri=url_for('static', filename='logo.webp'),
        )

    except Exception as e:
        print(f"❌ Erro ao carregar o PDF do simulado: {e}")
        flash("Ocorreu um erro ao abrir o PDF. Tente novamente.", "danger")
        return redirect('/aluno/simulados')
