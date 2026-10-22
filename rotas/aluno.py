# Arquivo: rotas/aluno.py
from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, logout_user
from postgrest.types import CountMethod
from banco_dados_aluno import supabase
from extensoes import limiter
from utils import safe_execute, aluno_required

aluno_bp = Blueprint('aluno', __name__)



@aluno_bp.route('/')
@limiter.exempt
def index():
    # Portão de entrada do app (ex-landing de apresentação, aposentada com o
    # fim do modelo pago): a raiz leva direto à tela de login — a versão
    # instalável (Electron) abre aqui. Alunos logados seguem à área do aluno.
    if current_user.is_authenticated:
        if current_user.role != 'aluno':
            logout_user()
            flash("A área administrativa roda em aplicativo dedicado (app_admin.py).", "warning")
            return redirect(url_for('auth.login_aluno'))
        return redirect(url_for('questao.resolver_questoes'))
    return redirect(url_for('auth.login_aluno'))




@aluno_bp.route('/aluno/tutoriais')
@aluno_required
def ver_tutoriais():
    # Agora apontando para o arquivo com nome genérico
    return render_template('aluno/tutoriais.html')




@aluno_bp.route('/aluno/painel')
@limiter.exempt
@aluno_required
def area_do_aluno():
    user_id = current_user.id
    fuso_br = timezone(timedelta(hours=-3))

    try:
        # 1. BUSCAR TOTAIS
        query_total = supabase.table("historico_respostas").select("*", count=CountMethod.exact).eq("id_usuario", str(user_id))
        res_total = safe_execute(query_total)
        total_resolvidas = res_total.count if res_total.count else 0

        query_acertos = supabase.table("historico_respostas").select("*", count=CountMethod.exact).eq("id_usuario", str(user_id)).eq("is_correct", True)
        res_acertos = safe_execute(query_acertos)
        acertos = res_acertos.count if res_acertos.count else 0

        taxa_acerto = round((acertos / total_resolvidas) * 100) if total_resolvidas > 0 else 0

        # 2. BUSCAR HISTÓRICO PARA GRÁFICO E OFENSIVA (Buscamos 'criado_em' E 'is_correct')
        query_historico = supabase.table("historico_respostas").select("criado_em, is_correct").eq("id_usuario", str(user_id)).limit(50000)
        res_historico = safe_execute(query_historico)
        historico = res_historico.data or []

        # --- LÓGICA DA OFENSIVA (STREAK) COM FUSO BRASÍLIA ---
        hoje_br = datetime.now(fuso_br).date()
        ontem_br = hoje_br - timedelta(days=1)
        
        datas_unicas_br = set()
        for item in historico:
            dt_utc = datetime.fromisoformat(item['criado_em'].replace('Z', '+00:00')) # type: ignore
            dt_br = dt_utc.astimezone(fuso_br)
            datas_unicas_br.add(dt_br.date())
        
        datas_ordenadas = sorted(list(datas_unicas_br), reverse=True)

        streak_count = 0
        if datas_ordenadas:
            if datas_ordenadas[0] == hoje_br or datas_ordenadas[0] == ontem_br:
                streak_count = 1
                for i in range(len(datas_ordenadas) - 1):
                    if (datas_ordenadas[i] - datas_ordenadas[i+1]).days == 1:
                        streak_count += 1
                    else:
                        break
        
        print(f"\n[SISTEMA OFENSIVA] Hoje em Brasília: {hoje_br} | Ofensiva Atual: {streak_count} dias")

        # 3. ORGANIZAR DADOS DO GRÁFICO (Agora preparado para 30 dias!)
        dados_grafico = {}
        for i in range(29, -1, -1):
            dia_calc = (datetime.now(fuso_br) - timedelta(days=i)).strftime('%d/%m')
            dados_grafico[dia_calc] = {'acertos': 0, 'erros': 0}

        for item in historico:
            data_iso = item.get('criado_em') # type: ignore
            if data_iso:
                dt_utc = datetime.fromisoformat(data_iso.replace('Z', '+00:00')) # type: ignore
                dt_br = dt_utc.astimezone(fuso_br) 
                dia_formatado = dt_br.strftime('%d/%m')
                
                # Se a data estiver nos últimos 30 dias, ele soma!
                if dia_formatado in dados_grafico:
                    if item.get('is_correct') is True: # type: ignore
                        dados_grafico[dia_formatado]['acertos'] += 1
                    elif item.get('is_correct') is False: # type: ignore
                        dados_grafico[dia_formatado]['erros'] += 1

        # Prepara as listas isoladas para o Chart.js no template
        labels_grafico = list(dados_grafico.keys())
        dados_acertos = [d['acertos'] for d in dados_grafico.values()]
        dados_erros = [d['erros'] for d in dados_grafico.values()]

        # --- NOVAS MÉTRICAS PARA O DASHBOARD PREMIUM ---
        hoje_resolvidas = 0
        semana_atual_count = 0
        semana_anterior_count = 0
        
        sete_dias_atras = hoje_br - timedelta(days=7)
        quatorze_dias_atras = hoje_br - timedelta(days=14)

        for item in historico:
            dt_utc = datetime.fromisoformat(item['criado_em'].replace('Z', '+00:00')) # type: ignore
            dt_br = dt_utc.astimezone(fuso_br).date()
            
            if dt_br == hoje_br:
                hoje_resolvidas += 1
            
            if dt_br > sete_dias_atras:
                semana_atual_count += 1
            elif quatorze_dias_atras < dt_br <= sete_dias_atras:
                semana_anterior_count += 1

        # Cálculo de evolução
        if semana_anterior_count > 0:
            evolucao_percentual = round(((semana_atual_count - semana_anterior_count) / semana_anterior_count) * 100)
        else:
            evolucao_percentual = semana_atual_count * 100 if semana_atual_count > 0 else 0

        # Nível de performance
        if taxa_acerto >= 80: performance_nivel = "Alto Desempenho"
        elif taxa_acerto >= 60: performance_nivel = "Bom Desempenho"
        elif taxa_acerto >= 40: performance_nivel = "Desempenho Regular"
        else: performance_nivel = "Precisa de Foco"

        return render_template('aluno/dashboard.html', 
                               total_resolvidas=total_resolvidas,
                               taxa_acerto=taxa_acerto,
                               labels_grafico=labels_grafico,
                               dados_acertos=dados_acertos,
                               dados_erros=dados_erros,
                               streak_count=streak_count,
                               hoje_resolvidas=hoje_resolvidas,
                               evolucao_percentual=evolucao_percentual,
                               performance_nivel=performance_nivel)


    except Exception as e:
        print(f"❌ Erro crítico ao carregar o painel do aluno: {e}")
        flash("Ocorreu uma instabilidade ao carregar alguns dos seus dados. Atualize a página.", "warning")
        return render_template('aluno/dashboard.html', 
                               total_resolvidas=0, 
                               taxa_acerto=0, 
                               labels_grafico=[], 
                               dados_acertos=[], 
                               dados_erros=[],
                               streak_count=0)



@aluno_bp.route('/aluno/api/set-meta', methods=['POST'])
@aluno_required
def set_meta():
    data = request.json
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400
        
    nova_meta = data.get('meta')
    if nova_meta is None:
        return jsonify({"error": "Meta não fornecida"}), 400
    
    try:
        # Atualiza no banco
        safe_execute(
            supabase.table("usuarios")
            .update({"meta_diaria": int(nova_meta)})
            .eq("id", str(current_user.id))
        )
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"❌ Erro ao salvar meta: {e}")
        return jsonify({"error": "Erro ao salvar meta diária."}), 500


@aluno_bp.route('/aluno/dashboard_detalhado')
@limiter.exempt
@aluno_required
def dashboard_detalhado():
    user_id = current_user.id
    fuso_br = timezone(timedelta(hours=-3))
    agora_br = datetime.now(fuso_br)

    try:
        # 1. BUSCAR TODA A HISTÓRIA DO ALUNO
        res_historico = safe_execute(
            supabase.table("historico_respostas")
            .select("id_questao, is_correct, criado_em")
            .eq("id_usuario", str(user_id))
            .order("criado_em", desc=True)
        )
        historico = res_historico.data or []

        if not historico:
            flash("Resolva algumas questões primeiro para gerar seu dashboard!", "info")
            return redirect(url_for('aluno.area_do_aluno'))

        # 2. BUSCAR METADADOS DAS QUESTÕES (Matéria e Tópico)
        # Para performance, vamos pegar apenas as questões que o aluno já respondeu
        ids_questoes = list(set([h['id_questao'] for h in historico]))
        
        # Como o array de IDs pode ser muito grande, vamos fazer em blocos de 500 se necessário
        # Mas para simplificar aqui, assumimos que o aluno não tem milhões de questões únicas ainda
        questoes_meta = {}
        for i in range(0, len(ids_questoes), 500):
            bloco_ids = ids_questoes[i:i+500]
            res_meta = safe_execute(
                supabase.table("view_questoes_completa")
                .select("id_questao, id_materia, nome_materia, id_topico, nome_topico")
                .in_("id_questao", bloco_ids)
            )
            for q in (res_meta.data or []):
                questoes_meta[q['id_questao']] = q

        # 3. PROCESSAMENTO DE DADOS (PYTHON POWER) 🐍
        desempenho_materia = {} # {id_materia: {nome, acertos, total, topicos: {id_t: {nome, acertos, total}}}}
        evolucao_30d = {} # {data_br: {id_materia: acertos}}
        
        # Inicializa os últimos 30 dias na evolução
        for i in range(29, -1, -1):
            dia = (agora_br - timedelta(days=i)).strftime('%d/%m')
            evolucao_30d[dia] = {}

        for h in historico:
            if not h.get('id_questao'):
                continue
                
            meta = questoes_meta.get(h['id_questao'])
            if not meta: continue

            id_m = meta.get('id_materia')
            id_t = meta.get('id_topico')
            
            # Ignora histórico de questões que perderam vínculo com matéria/tópico
            if not id_m or not id_t:
                continue

            nome_m = meta.get('nome_materia') or "Matéria Indefinida"
            nome_t = meta.get('nome_topico') or "Tópico Indefinido"
            correto = h.get('is_correct', False)

            # Agregação para Gráfico e Metas (Processar data primeiro!)
            try:
                dt_str = h['criado_em'].replace('Z', '+00:00')
                dt_utc = datetime.fromisoformat(dt_str)
                if dt_utc.tzinfo is None:
                    from datetime import timezone as dt_tz
                    dt_utc = dt_utc.replace(tzinfo=dt_tz.utc)
                dt_br = dt_utc.astimezone(fuso_br)
            except Exception:
                dt_br = agora_br
                
            dia_br = dt_br.strftime('%d/%m')

            # Agregação por Matéria
            if id_m not in desempenho_materia:
                desempenho_materia[id_m] = {
                    'id_materia': id_m,
                    'nome': nome_m, 'acertos': 0, 'total': 0, 'topicos': {},
                    'ultima_resolucao': dt_br
                }
            
            desempenho_materia[id_m]['total'] += 1
            if correto: desempenho_materia[id_m]['acertos'] += 1
            if dt_br > desempenho_materia[id_m]['ultima_resolucao']:
                desempenho_materia[id_m]['ultima_resolucao'] = dt_br

            # Agregação por Tópico
            if id_t not in desempenho_materia[id_m]['topicos']:
                desempenho_materia[id_m]['topicos'][id_t] = {
                    'nome': nome_t, 'acertos': 0, 'total': 0
                }
            
            desempenho_materia[id_m]['topicos'][id_t]['total'] += 1
            if correto: desempenho_materia[id_m]['topicos'][id_t]['acertos'] += 1

            # Agregação para Gráfico (Últimos 30 dias)
            if dia_br in evolucao_30d:
                if id_m not in evolucao_30d[dia_br]:
                    evolucao_30d[dia_br][id_m] = 0
                if correto:
                    evolucao_30d[dia_br][id_m] += 1

        # 4. FORMATAÇÃO PARA O TEMPLATE
        lista_materias = []
        pontos_atencao = []
        alertas_revisao = []
        total_resolvidas_global = len(historico)
        total_acertos_global = sum(1 for h in historico if h['is_correct'])
        
        for id_m, dados in desempenho_materia.items():
            dados['taxa'] = round((dados['acertos'] / dados['total']) * 100)
            
            # Cálculo da Curva do Esquecimento
            dias_atraso = (agora_br - dados['ultima_resolucao']).days
            dados['dias_atraso'] = dias_atraso
            
            if dias_atraso >= 4:
                status = "REVISAR"
                cor = "warning"
                if dias_atraso >= 8:
                    status = "ALERTA"
                    cor = "orange" # Custom color handled in CSS
                if dias_atraso >= 15:
                    status = "CRÍTICO"
                    cor = "danger"
                
                alertas_revisao.append({
                    'id_materia': id_m,
                    'nome': dados['nome'],
                    'dias': dias_atraso,
                    'status': status,
                    'cor': cor
                })
            
            # Formata tópicos
            topicos_lista = []
            for id_t, dt in dados['topicos'].items():
                dt['taxa'] = round((dt['acertos'] / dt['total']) * 100)
                dt['id_materia'] = id_m
                dt['id_topico'] = id_t
                topicos_lista.append(dt)
                
                # Alerta de revisão (Menos de 60% de acerto e pelo menos 5 questões - A pedido do usuário)
                if dt['taxa'] < 60 and dt['total'] >= 5:
                    pontos_atencao.append({
                        'materia': dados['nome'], 'topico': dt['nome'], 
                        'taxa': dt['taxa'], 'total': dt['total'],
                        'id_materia': id_m, 'id_topico': id_t
                    })
            
            dados['topicos_lista'] = sorted(topicos_lista, key=lambda x: x['taxa'])
            lista_materias.append(dados)

        # Ordenações
        lista_materias = sorted(lista_materias, key=lambda x: x['total'], reverse=True)
        pontos_atencao = sorted(pontos_atencao, key=lambda x: (x['taxa'], -int(x['total'])))[:10]
        alertas_revisao = sorted(alertas_revisao, key=lambda x: x['dias'], reverse=True)[:5] # Top 5 mais urgentes
        
        # Filtro para Melhor Matéria: Deve ter pelo menos 5 questões respondidas (A pedido do usuário)
        materias_para_melhor = [m for m in lista_materias if m['total'] >= 5]
        melhor_materia = max(materias_para_melhor, key=lambda x: (x['taxa'], x['total'])) if materias_para_melhor else None

        # 5. DADOS PARA O CALENDÁRIO DE METAS (Mês Atual)
        concluidos_por_dia = {}
        primeiro_dia_mes = agora_br.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        for h in historico:
            if not h.get('criado_em'):
                continue
            try:
                dt_utc = datetime.fromisoformat(h['criado_em'].replace('Z', '+00:00'))
                if dt_utc.tzinfo is None:
                    from datetime import timezone as dt_tz
                    dt_utc = dt_utc.replace(tzinfo=dt_tz.utc)
                dt_br = dt_utc.astimezone(fuso_br)
                if dt_br >= primeiro_dia_mes:
                    dia_iso = dt_br.strftime('%Y-%m-%d')
                    concluidos_por_dia[dia_iso] = concluidos_por_dia.get(dia_iso, 0) + 1
            except Exception:
                pass

        # 6. PREPARAÇÃO DO GRÁFICO MULTI-LINHA
        labels_grafico = list(evolucao_30d.keys())
        datasets = []
        
        # Cores vibrantes para as matérias
        cores_nobres = [
            '#3b82f6', '#10b981', '#ef4444', '#f59e0b', '#8b5cf6', 
            '#06b6d4', '#f97316', '#ec4899', '#6366f1', '#22c55e',
            '#a855f7', '#0ea5e9', '#f43f5e', '#d946ef', '#14b8a6'
        ]
        
        for idx, m_meta in enumerate(lista_materias[:12]): # Pegamos as 12 principais para não poluir
            m_id = m_meta.get('id_materia')
            
            data_points = []
            for dia in labels_grafico:
                data_points.append(evolucao_30d[dia].get(m_id, 0))
            
            datasets.append({
                'label': m_meta['nome'],
                'data': data_points,
                'borderColor': cores_nobres[idx % len(cores_nobres)],
                'backgroundColor': cores_nobres[idx % len(cores_nobres)],
                'id_materia': m_id
            })

        return render_template('aluno/estatisticas.html',
                               materias=lista_materias,
                               pontos_atencao=pontos_atencao,
                               melhor_materia=melhor_materia,
                               datasets=datasets,
                               labels_grafico=labels_grafico,
                               total_resolvidas=total_resolvidas_global,
                               total_acertos=total_acertos_global,
                               taxa_global=round((total_acertos_global/total_resolvidas_global)*100) if total_resolvidas_global > 0 else 0,
                               meta_diaria=getattr(current_user, 'meta_diaria', 0),
                               concluidos_por_dia=concluidos_por_dia,
                               alertas_revisao=alertas_revisao)

    except Exception as e:
        print(f"❌ Erro no Dashboard Detalhado: {e}")
        flash("Erro ao processar suas estatísticas detalhadas.", "danger")
        return redirect(url_for('aluno.area_do_aluno'))
