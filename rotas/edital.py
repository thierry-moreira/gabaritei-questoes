import random
from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, request, redirect, flash, jsonify
from flask_login import current_user

from banco_dados_aluno import supabase
from extensoes import limiter
from utils import safe_execute, aluno_required, premium_required

edital_bp = Blueprint('edital', __name__)

META_MINIMA_QUESTOES = 5
META_MAXIMA_QUESTOES = 30
PESO_DESEMPENHO = 0.5
PENALIDADE_RECENTE = 20
PENALIDADE_RECENTE_DECAI = 10
BONUS_NOVIDADE = 15
LIMIAR_DOMINIO = 0.8
INTERVALO_REVISIAO_DIAS = 3

PESO_MATERIA_MUITO_RUIM = 100
PESO_MATERIA_RUIM = 75
PESO_MATERIA_REGULAR = 50
PESO_MATERIA_BOM = 25


def _calcular_desempenho_materia(id_edital_materia):
    res = safe_execute(
        supabase.table("editais_materias")
        .select("questoes_resolvidas, questoes_acertadas")
        .eq("id_edital_materia", id_edital_materia)
        .single()
    )
    if not res.data:
        return 0.0

    resolvidas = res.data.get('questoes_resolvidas') or 0
    acertadas = res.data.get('questoes_acertadas') or 0

    if resolvidas == 0:
        return 0.0

    return acertadas / resolvidas


def _selecionar_proxima_materia(id_edital, materias_ids):
    if not materias_ids:
        return None

    if len(materias_ids) == 1:
        return materias_ids[0]

    pesos = []
    for id_mat in materias_ids:
        taxa = _calcular_desempenho_materia(id_mat)

        if taxa <= 0.4:
            peso = PESO_MATERIA_MUITO_RUIM
        elif taxa <= 0.6:
            peso = PESO_MATERIA_RUIM
        elif taxa <= 0.8:
            peso = PESO_MATERIA_REGULAR
        else:
            peso = PESO_MATERIA_BOM

        pesos.append(peso)

    total = sum(pesos)
    if total == 0:
        return random.choice(materias_ids)

    sorteio = random.uniform(0, total)
    acumulado = 0
    for i, id_mat in enumerate(materias_ids):
        acumulado += pesos[i]
        if sorteio <= acumulado:
            return id_mat

    return materias_ids[-1]


def _calcular_peso_topico(id_edital_topico, historico_topicos=None):
    historico_topicos = historico_topicos or []

    res = safe_execute(
        supabase.table("editais_topicos")
        .select("questoes_resolvidas, questoes_acertadas, ultimo_estudado_em, vezes_estudado")
        .eq("id_edital_topico", id_edital_topico)
        .single()
    )

    if not res.data:
        return 50

    resolvidas = res.data.get('questoes_resolvidas') or 0
    acertadas = res.data.get('questoes_acertadas') or 0
    ultimo_estudado = res.data.get('ultimo_estudado_em')

    peso = 50.0

    if resolvidas > 0:
        taxa_acerto = acertadas / resolvidas
        peso += (1.0 - taxa_acerto) * 100 * PESO_DESEMPENHO
    else:
        peso += BONUS_NOVIDADE

    if historico_topicos:
        try:
            idx = historico_topicos.index(id_edital_topico)
            if idx == 0:
                peso -= PENALIDADE_RECENTE
            elif idx == 1:
                peso -= PENALIDADE_RECENTE_DECAI
        except ValueError:
            pass

    if resolvidas > 0:
        taxa_acerto = acertadas / resolvidas
        if taxa_acerto >= LIMIAR_DOMINIO:
            if ultimo_estudado:
                data_ultimo = datetime.fromisoformat(ultimo_estudado.replace('Z', '+00:00'))
                dias_desde = (datetime.now(timezone.utc) - data_ultimo).days
                if dias_desde < INTERVALO_REVISIAO_DIAS:
                    peso -= 30
                else:
                    peso -= 10
            else:
                peso -= 10

    return max(0, peso)


def _calcular_meta_dinamica(id_edital_topico):
    res = safe_execute(
        supabase.table("editais_topicos")
        .select("questoes_resolvidas, questoes_acertadas")
        .eq("id_edital_topico", id_edital_topico)
        .single()
    )

    if not res.data:
        return 15

    resolvidas = res.data.get('questoes_resolvidas') or 0
    acertadas = res.data.get('questoes_acertadas') or 0

    if resolvidas == 0:
        return 20

    taxa_acerto = acertadas / resolvidas
    taxa_percent = taxa_acerto * 100

    meta = round(10 + (100 - taxa_percent) * 0.25)
    return max(META_MINIMA_QUESTOES, min(META_MAXIMA_QUESTOES, meta))


def _avancar_ciclo_edital(id_edital, marcar_concluido=False):
    res_prog = safe_execute(
        supabase.table("editais_progresso").select("*").eq("id_edital", id_edital).single()
    )
    progresso = res_prog.data
    if not progresso:
        return False, "Erro ao carregar progresso.", None

    id_mat_atual = progresso['materia_atual_id']
    id_top_atual = progresso['topico_atual_id']
    historico_topicos = progresso.get('historico_topicos') or []

    if marcar_concluido:
        safe_execute(
            supabase.table("editais_topicos").update({"concluido": True})
            .eq("id_edital_topico", id_top_atual)
        )

    if isinstance(historico_topicos, list):
        historico_topicos = [t for t in historico_topicos if t != id_top_atual]
    else:
        historico_topicos = []
    historico_topicos.insert(0, id_top_atual)
    historico_topicos = historico_topicos[:5]

    res_materias = safe_execute(
        supabase.table("editais_materias")
        .select("id_edital_materia")
        .eq("id_edital", id_edital)
        .order("ordem")
    )
    todas_materias = res_materias.data or []
    materias_ids = [m['id_edital_materia'] for m in todas_materias]

    if not materias_ids:
        return False, "Nenhuma matéria encontrada no edital.", None

    id_mat_prox = _selecionar_proxima_materia(id_edital, materias_ids)

    res_topicos = safe_execute(
        supabase.table("editais_topicos")
        .select("id_edital_topico")
        .eq("id_edital_materia", id_mat_prox)
        .eq("concluido", False)
    )
    topicos_disponiveis = res_topicos.data or []

    if not topicos_disponiveis:
        safe_execute(
            supabase.table("editais_topicos").update({"concluido": False})
            .eq("id_edital_materia", id_mat_prox)
        )
        res_topicos = safe_execute(
            supabase.table("editais_topicos")
            .select("id_edital_topico")
            .eq("id_edital_materia", id_mat_prox)
        )
        topicos_disponiveis = res_topicos.data or []

    if not topicos_disponiveis:
        return False, "Erro: nenhum tópico disponível.", None

    topicos_com_peso = []
    for t in topicos_disponiveis:
        peso = _calcular_peso_topico(t['id_edital_topico'], historico_topicos)
        topicos_com_peso.append((t['id_edital_topico'], peso))

    topicos_com_peso.sort(key=lambda x: x[1], reverse=True)

    top_candidatos = topicos_com_peso[:min(3, len(topicos_com_peso))]
    if len(top_candidatos) > 1:
        total_peso = sum(p for _, p in top_candidatos)
        sorteio = random.uniform(0, total_peso)
        acumulado = 0
        id_top_prox = top_candidatos[0][0]
        for tid, p in top_candidatos:
            acumulado += p
            if sorteio <= acumulado:
                id_top_prox = tid
                break
    else:
        id_top_prox = top_candidatos[0][0]

    meta_dinamica = _calcular_meta_dinamica(id_top_prox)

    # Execute RPC separately since it returns a request builder, not a value
    safe_execute(supabase.rpc("increment", {"row_id": id_top_prox}))
    
    safe_execute(
        supabase.table("editais_topicos").update({
            "ultimo_estudado_em": datetime.now(timezone.utc).isoformat(),
            # "vezes_estudado" is updated by the RPC above
        }).eq("id_edital_topico", id_top_prox)
    )
    
    res_times = safe_execute(
        supabase.table("editais_topicos")
        .select("vezes_estudado")
        .eq("id_edital_topico", id_top_prox)
        .single()
    )
    if res_times.data:
        vezes = (res_times.data.get('vezes_estudado') or 0) + 1
        safe_execute(
            supabase.table("editais_topicos").update({
                "vezes_estudado": vezes
            }).eq("id_edital_topico", id_top_prox)
        )

    safe_execute(supabase.table("editais_progresso").update({
        "materia_atual_id": id_mat_prox,
        "topico_atual_id": id_top_prox,
        "questoes_resolvidas_neste_topico": 0,
        "meta_dinamica": meta_dinamica,
        "historico_topicos": historico_topicos
    }).eq("id_edital", id_edital))

    res_nome_mat = safe_execute(
        supabase.table("editais_materias")
        .select("materias(nome_materia)")
        .eq("id_edital_materia", id_mat_prox)
        .single()
    )
    nome_mat = res_nome_mat.data['materias']['nome_materia'] if res_nome_mat.data else ""

    msg = f"Avançando para {nome_mat} — meta: {meta_dinamica} questões."
    return True, msg, meta_dinamica


@edital_bp.route('/aluno/editais', methods=['GET'])
@limiter.exempt
@aluno_required
@premium_required
def painel_editais():
    res_editais = safe_execute(
        supabase.table("editais_ciclo").select("*").eq("id_usuario", current_user.id).order("criado_em", desc=True)
    )
    editais = res_editais.data or []

    materias = safe_execute(supabase.table("materias").select("*").order("nome_materia")).data or []

    return render_template('editais/index.html', editais=editais, materias=materias)


@edital_bp.route('/aluno/editais/criar', methods=['POST'])
@limiter.exempt
@aluno_required
@premium_required
def criar_edital():
    titulo = request.form.get('titulo')
    materias = request.form.getlist('materias[]')
    topicos_list = request.form.getlist('topicos[]')

    id_edital = None  # Initialize to avoid "possibly unbound" error

    try:
        res_edital = safe_execute(supabase.table('editais_ciclo').insert({
            'id_usuario': current_user.id,
            'titulo': titulo
        }))
        id_edital = res_edital.data[0]['id_edital']

        ordem_materia = 1
        primeira_materia_id = None
        primeiro_topico_id = None

        for i in range(len(materias)):
            id_mat = int(materias[i])
            ids_topicos_str = topicos_list[i] if i < len(topicos_list) else ''

            if not ids_topicos_str:
                continue

            res_mat = safe_execute(supabase.table('editais_materias').insert({
                'id_edital': id_edital,
                'id_materia': id_mat,
                'id_usuario': current_user.id,
                'ordem': ordem_materia
            }))
            id_edital_materia = res_mat.data[0]['id_edital_materia']

            if ordem_materia == 1:
                primeira_materia_id = id_edital_materia

            ids_topicos = ids_topicos_str.split(',')
            for j, t_id in enumerate(ids_topicos):
                if not t_id.strip():
                    continue
                res_top = safe_execute(supabase.table('editais_topicos').insert({
                    'id_edital_materia': id_edital_materia,
                    'id_topico': int(t_id),
                    'id_usuario': current_user.id
                }))

                if ordem_materia == 1 and j == 0 and primeira_materia_id:
                    primeiro_topico_id = res_top.data[0]['id_edital_topico']

            ordem_materia += 1

        if primeira_materia_id and primeiro_topico_id:
            meta_inicial = _calcular_meta_dinamica(primeiro_topico_id)

            safe_execute(supabase.table('editais_progresso').insert({
                'id_edital': id_edital,
                'id_usuario': current_user.id,
                'materia_atual_id': primeira_materia_id,
                'topico_atual_id': primeiro_topico_id,
                'meta_dinamica': meta_inicial,
                'historico_topicos': []
            }))
            flash(f"Edital '{titulo}' criado! O ciclo adaptativo está pronto.", "success")
        else:
            safe_execute(supabase.table('editais_ciclo').delete().eq('id_edital', id_edital))
            flash("Você precisa selecionar ao menos um assunto para montar o edital.", "warning")

    except Exception as e:
        print(f"❌ Erro ao criar edital: {e}")
        if id_edital is not None:
            safe_execute(supabase.table('editais_ciclo').delete().eq('id_edital', id_edital))
        flash("Erro interno ao criar o edital. Verifique os dados e tente novamente.", "danger")

    return redirect('/aluno/editais')


@edital_bp.route('/aluno/editais/estudar/<int:id_edital>')
@limiter.exempt
@aluno_required
@premium_required
def estudar_edital(id_edital):
    try:
        res_edital_check = safe_execute(
            supabase.table('editais_ciclo')
            .select('id_edital')
            .eq('id_edital', id_edital)
            .eq('id_usuario', current_user.id)
            .single()
        )
        if not res_edital_check.data:
            flash("Edital não encontrado ou sem permissão de acesso.", "warning")
            return redirect('/aluno/editais')

        res_progresso = safe_execute(
            supabase.table('editais_progresso').select('*').eq('id_edital', id_edital).single()
        )
        progresso = res_progresso.data

        if not progresso:
            flash("Erro ao carregar o progresso do edital.", "danger")
            return redirect('/aluno/editais')

        id_edital_materia_atual = progresso.get('materia_atual_id')
        id_edital_topico_atual = progresso.get('topico_atual_id')
        meta_dinamica = progresso.get('meta_dinamica') or 10
        feitas_agora = progresso.get('questoes_resolvidas_neste_topico') or 0

        if not id_edital_topico_atual:
            flash("🎉 Parabéns! Você concluiu 100% deste edital!", "success")
            return redirect('/aluno/editais')

        res_mat = safe_execute(
            supabase.table('editais_materias')
            .select('materias(nome_materia)')
            .eq('id_edital_materia', id_edital_materia_atual).single()
        )

        res_top = safe_execute(
            supabase.table('editais_topicos')
            .select('id_topico, topicos(nome_topico)')
            .eq('id_edital_topico', id_edital_topico_atual).single()
        )

        real_id_topico = res_top.data['id_topico']
        nome_materia = res_mat.data['materias']['nome_materia']
        nome_topico = res_top.data['topicos']['nome_topico']

        res_hist = safe_execute(
            supabase.table('historico_respostas').select('id_questao').eq('id_usuario', current_user.id)
        )
        ids_feitos = [h['id_questao'] for h in (res_hist.data or [])]

        query_q = supabase.table('view_questoes_completa').select('*').eq('id_topico', real_id_topico)

        if ids_feitos:
            query_q = query_q.not_.in_('id_questao', ids_feitos)

        res_q = safe_execute(query_q.limit(50))
        pool_questoes = res_q.data or []

        questao = None
        if pool_questoes:
            questao = random.choice(pool_questoes)
        else:
            success, msg, nova_meta = _avancar_ciclo_edital(id_edital, marcar_concluido=True)
            if success:
                flash("Todas as questões inéditas deste tópico foram concluídas. Avançando...", "info")
            return redirect(f'/aluno/editais/estudar/{id_edital}')

        if questao:
            if not questao.get('texto_base'):
                questao['texto_base'] = ""

            res_alt = safe_execute(
                supabase.table('alternativas_questao').select('*').eq('id_questao', questao['id_questao'])
            )
            questao['alternativas_questao'] = sorted(res_alt.data or [], key=lambda x: x.get('letra', ''))

        return render_template('editais/estudar.html',
                               id_edital=id_edital,
                               materia=nome_materia,
                               topico=nome_topico,
                               meta=meta_dinamica,
                               feitas=feitas_agora,
                               questao=questao)

    except Exception as e:
        import traceback
        print(f"❌ Erro na Rota Estudar Edital: {e}")
        print(f"❌ Traceback completo:\n{traceback.format_exc()}")
        flash("Erro ao carregar a questão do ciclo.", "danger")
        return redirect('/aluno/editais')


@edital_bp.route('/aluno/editais/responder', methods=['POST'])
@limiter.exempt
@aluno_required
@premium_required
def responder_edital():
    dados = request.get_json()
    id_edital = dados.get('id_edital')
    id_questao = dados.get('id_questao')
    letra_escolhida = dados.get('alternativa')

    res_ownership = safe_execute(
        supabase.table('editais_ciclo').select('id_edital')
        .eq('id_edital', id_edital).eq('id_usuario', current_user.id).single()
    )
    if not res_ownership.data:
        return jsonify({"sucesso": False, "erro": "Edital não encontrado ou sem permissão."}), 403

    try:
        query_alt = supabase.table("alternativas_questao").select(
            "id_alternativa, letra, is_correct"
        ).eq("id_questao", id_questao).order("letra")
        res_alt = safe_execute(query_alt)
        alternativas = res_alt.data or []

        letra_correta = next((a['letra'] for a in alternativas if a['is_correct']), None)
        alt_marcada = next((a['id_alternativa'] for a in alternativas if a['letra'] == letra_escolhida), None)
        foi_correta = (letra_escolhida == letra_correta)

        res_q = safe_execute(
            supabase.table("questoes").select("comentario_gabarito")
            .eq("id_questao", id_questao).single()
        )
        comentario = res_q.data.get('comentario_gabarito') if res_q.data else "Sem comentário."

        safe_execute(supabase.table("historico_respostas").insert({
            "id_usuario": current_user.id,
            "id_questao": id_questao,
            "is_correct": foi_correta,
            "id_alternativa_marcada": alt_marcada
        }))

        res_prog = safe_execute(
            supabase.table("editais_progresso").select("*").eq("id_edital", id_edital).single()
        )
        progresso = res_prog.data

        id_mat_atual = progresso['materia_atual_id']
        id_top_atual = progresso['topico_atual_id']
        resolvidas_topico = (progresso.get('questoes_resolvidas_neste_topico') or 0) + 1
        meta_dinamica = progresso.get('meta_dinamica') or 10

        res_topico_stats = safe_execute(
            supabase.table("editais_topicos")
            .select("questoes_resolvidas, questoes_acertadas")
            .eq("id_edital_topico", id_top_atual).single()
        )
        q_res_t = (res_topico_stats.data.get('questoes_resolvidas') or 0) + 1
        q_ac_t = (res_topico_stats.data.get('questoes_acertadas') or 0) + (1 if foi_correta else 0)
        safe_execute(
            supabase.table("editais_topicos").update({
                "questoes_resolvidas": q_res_t,
                "questoes_acertadas": q_ac_t
            }).eq("id_edital_topico", id_top_atual)
        )

        res_mat_stats = safe_execute(
            supabase.table("editais_materias")
            .select("questoes_resolvidas, questoes_acertadas")
            .eq("id_edital_materia", id_mat_atual).single()
        )
        q_res_m = (res_mat_stats.data.get('questoes_resolvidas') or 0) + 1
        q_ac_m = (res_mat_stats.data.get('questoes_acertadas') or 0) + (1 if foi_correta else 0)
        safe_execute(
            supabase.table("editais_materias").update({
                "questoes_resolvidas": q_res_m,
                "questoes_acertadas": q_ac_m
            }).eq("id_edital_materia", id_mat_atual)
        )

        ciclo_avancou = False
        msg_avanco = ""

        if resolvidas_topico >= meta_dinamica:
            ciclo_avancou, msg_avanco, _ = _avancar_ciclo_edital(id_edital)
        else:
            safe_execute(supabase.table("editais_progresso").update({
                "questoes_resolvidas_neste_topico": resolvidas_topico
            }).eq("id_edital", id_edital))

        return jsonify({
            "sucesso": True,
            "correta": foi_correta,
            "letra_correta": letra_correta,
            "comentario": comentario,
            "ciclo_avancou": ciclo_avancou,
            "msg_avanco": msg_avanco
        })

    except Exception as e:
        print(f"❌ Erro ao responder ciclo: {e}")
        return jsonify({"sucesso": False, "erro": "Erro interno ao processar resposta."}), 500


@edital_bp.route('/aluno/editais/pular/<int:id_edital>', methods=['POST'])
@limiter.exempt
@aluno_required
@premium_required
def pular_topico_edital(id_edital):
    try:
        success, msg, _ = _avancar_ciclo_edital(id_edital, marcar_concluido=True)

        if success:
            flash("Tópico pulado! O sistema avançou para o próximo assunto do seu Edital.", "info")
        else:
            flash("Erro ao tentar pular o assunto.", "danger")

        return redirect(f'/aluno/editais/estudar/{id_edital}')

    except Exception as e:
        print(f"Erro ao pular tópico: {e}")
        flash("Erro ao tentar pular o assunto.", "danger")
        return redirect(f'/aluno/editais/estudar/{id_edital}')


@edital_bp.route('/aluno/editais/dashboard/<int:id_edital>')
@limiter.exempt
@aluno_required
@premium_required
def dashboard_edital(id_edital):
    try:
        res_edital = safe_execute(
            supabase.table("editais_ciclo").select("*")
            .eq("id_edital", id_edital).eq("id_usuario", current_user.id).single()
        )
        edital = res_edital.data
        if not edital:
            flash("Edital não encontrado.", "danger")
            return redirect('/aluno/editais')

        res_prog = safe_execute(
            supabase.table("editais_progresso").select("historico_topicos")
            .eq("id_edital", id_edital).single()
        )
        historico_topicos = (res_prog.data.get('historico_topicos') or []) if res_prog.data else []

        res_materias = safe_execute(
            supabase.table("editais_materias")
            .select("*, materias(nome_materia), editais_topicos(*, topicos(nome_topico))")
            .eq("id_edital", id_edital)
            .order("ordem")
        )
        materias_raw = res_materias.data or []

        total_resolvidas = 0
        total_acertos = 0
        pontos_atencao = []
        topicos_prioridade = []

        for m in materias_raw:
            m['nome'] = m['materias']['nome_materia']

            q_res_m = m.get('questoes_resolvidas') or 0
            q_ac_m = m.get('questoes_acertadas') or 0

            m['taxa_acerto'] = round((q_ac_m / q_res_m) * 100) if q_res_m > 0 else 0

            taxa_m = q_ac_m / q_res_m if q_res_m > 0 else 0
            if taxa_m <= 0.4:
                m['peso_materia'] = PESO_MATERIA_MUITO_RUIM
                m['nivel'] = 'muito_ruim'
            elif taxa_m <= 0.6:
                m['peso_materia'] = PESO_MATERIA_RUIM
                m['nivel'] = 'ruim'
            elif taxa_m <= 0.8:
                m['peso_materia'] = PESO_MATERIA_REGULAR
                m['nivel'] = 'regular'
            else:
                m['peso_materia'] = PESO_MATERIA_BOM
                m['nivel'] = 'bom'

            total_resolvidas += q_res_m
            total_acertos += q_ac_m

            for t in m.get('editais_topicos', []):
                t['nome'] = t['topicos']['nome_topico']

                q_res_t = t.get('questoes_resolvidas') or 0
                q_ac_t = t.get('questoes_acertadas') or 0

                t['taxa_acerto'] = round((q_ac_t / q_res_t) * 100) if q_res_t > 0 else 0

                t['peso_adaptativo'] = round(_calcular_peso_topico(
                    t['id_edital_topico'], historico_topicos
                ), 1)
                t['meta_dinamica'] = _calcular_meta_dinamica(t['id_edital_topico'])

                if t['peso_adaptativo'] >= 80:
                    t['nivel_prioridade'] = 'alta'
                    t['badge_cor'] = 'danger'
                elif t['peso_adaptativo'] >= 50:
                    t['nivel_prioridade'] = 'media'
                    t['badge_cor'] = 'warning'
                else:
                    t['nivel_prioridade'] = 'baixa'
                    t['badge_cor'] = 'success'

                topicos_prioridade.append(t)

                if q_res_t >= 3 and t['taxa_acerto'] < 60:
                    pontos_atencao.append({
                        'materia': m['nome'],
                        'topico': t['nome'],
                        'taxa': t['taxa_acerto'],
                        'resolvidas': q_res_t,
                        'id_materia': m['id_materia'],
                        'id_topico': t['id_topico'],
                        'peso_adaptativo': t['peso_adaptativo'],
                        'meta_dinamica': t['meta_dinamica']
                    })

        pontos_atencao = sorted(pontos_atencao, key=lambda x: x['taxa'])
        topicos_prioridade = sorted(topicos_prioridade, key=lambda x: x['peso_adaptativo'], reverse=True)

        desempenho_geral = round((total_acertos / total_resolvidas) * 100) if total_resolvidas > 0 else 0

        return render_template('editais/dashboard.html',
                               edital=edital,
                               materias=materias_raw,
                               total_resolvidas=total_resolvidas,
                               desempenho_geral=desempenho_geral,
                               pontos_atencao=pontos_atencao,
                               topicos_prioridade=topicos_prioridade)

    except Exception as e:
        print(f"❌ Erro ao carregar dashboard do edital: {e}")
        flash("Erro ao carregar o relatório de desempenho.", "danger")
        return redirect('/aluno/editais')


@edital_bp.route('/aluno/editais/excluir/<id_edital>', methods=['POST'])
@limiter.exempt
@aluno_required
@premium_required
def excluir_edital(id_edital):
    try:
        query_del = supabase.table("editais_ciclo").delete().eq("id_edital", int(id_edital)).eq("id_usuario", current_user.id)
        res = safe_execute(query_del)

        if res.data:
            flash("Edital e todo o seu progresso foram excluídos com sucesso!", "success")
        else:
            flash("Você não tem permissão para excluir este edital ou ele já não existe.", "warning")

    except Exception as e:
        print(f"❌ Erro ao excluir edital {id_edital}: {e}")
        flash("Erro de conexão ao tentar excluir o edital.", "danger")

    return redirect('/aluno/editais')