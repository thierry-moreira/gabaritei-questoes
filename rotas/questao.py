from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort, current_app, flash
from flask_login import current_user, logout_user
import re
from typing import Any

from postgrest import CountMethod

from banco_dados_aluno import supabase
from extensoes import MODELO_GPT, TEMPERATURE_GPT, csrf, client_gpt, limiter
from utils import safe_execute, aluno_required, premium_required, slugify

questao_bp = Blueprint('questao', __name__)


@questao_bp.route('/aluno/responder', methods=['POST'])
@limiter.limit("60 per minute")
@aluno_required
def responder_questao():
    dados = request.get_json()
    questao_id = dados.get('questao_id')
    letra_escolhida = dados.get('alternativa')
    user_id = str(current_user.id)

    query_alt = supabase.table("alternativas_questao")\
        .select("id_alternativa, letra, is_correct")\
        .eq("id_questao", questao_id)\
        .order("letra")
    
    res_alt = safe_execute(query_alt)
    alternativas = res_alt.data or []
    
    letra_correta = next((a['letra'] for a in alternativas if a['is_correct']), None)
    alt_marcada = next((a['id_alternativa'] for a in alternativas if a['letra'] == letra_escolhida), None)
    
    if not alt_marcada:
        return jsonify({"success": False, "error": "Alternativa inválida ou não selecionada."}), 400
        
    foi_correta = (letra_escolhida == letra_correta)

    query_q = supabase.table("questoes").select("comentario_gabarito").eq("id_questao", questao_id).single()
    res_q = safe_execute(query_q)
    comentario = res_q.data.get('comentario_gabarito') if res_q.data else "Sem comentário disponível."

    try:
        query_hist = supabase.table("historico_respostas").insert({
            "id_usuario": user_id,
            "id_questao": questao_id,
            "is_correct": foi_correta,
            "id_alternativa_marcada": alt_marcada
        })
        safe_execute(query_hist)
    except Exception as e:
        print(f"❌ ERRO CRÍTICO NO PROCESSAMENTO: {e}")
        if current_app.config.get('TESTING'):
            raise e

    return jsonify({
        "sucesso": True,
        "correta": foi_correta,
        "letra_correta": letra_correta,
        "comentario": comentario
    })


@questao_bp.route('/api/responder_publico', methods=['POST'])
@limiter.limit("20 per minute")
def responder_publico():
    from flask import session
    dados = request.get_json()
    questao_id = int(dados.get('questao_id'))
    letra_escolhida = dados.get('alternativa')

    questoes_vistas = list(set(int(x) for x in session.get('anon_questoes', []) if str(x).isdigit()))
    
    if len(questoes_vistas) >= 5 and questao_id not in questoes_vistas:
        return jsonify({"success": False, "error": "Você atingiu o limite de 5 questões gratuitas. Crie uma conta para continuar estudando!"}), 403

    query_alt = supabase.table("alternativas_questao")\
        .select("*")\
        .eq("id_questao", questao_id)\
        .order("letra")
    res_alt = safe_execute(query_alt)
    alternativas = res_alt.data or []
    
    letra_correta = next((a['letra'] for a in alternativas if a['is_correct']), None)
    foi_correta = (letra_escolhida == letra_correta)
    
    if questao_id not in questoes_vistas:
        questoes_vistas.append(questao_id)
        session['anon_questoes'] = questoes_vistas
        session.modified = True
        
        try:
            safe_execute(supabase.table("historico_respostas_anonimo").insert({
                "id_questao": questao_id,
                "is_correct": foi_correta
            }))
        except Exception as e:
            print(f"Erro silenciado ao gravar resposta anônima: {e}")
            if current_app.config.get('TESTING'):
                raise e

    return jsonify({
        "sucesso": True,
        "correta": foi_correta,
        "letra_correta": letra_correta
    })


@questao_bp.route('/aluno/questoes', methods=['GET'])
@questao_bp.route('/questoes/<materia_slug>')
@questao_bp.route('/questoes/<materia_slug>/<topico_slug>')
@limiter.exempt
def resolver_questoes(materia_slug=None, topico_slug=None):
    if current_user.is_authenticated and current_user.role != 'aluno':
        logout_user()
        flash("A área administrativa roda em aplicativo dedicado (app_admin.py).", "warning")
        return redirect(url_for('auth.login_aluno'))
    
    filtros_salvos = []
    if current_user.is_authenticated:
        res_filtros = safe_execute(
            supabase.table("filtros_salvos")
            .select("*")
            .eq("id_usuario", current_user.id)
            .order("criado_em", desc=True)
        )
        filtros_salvos = res_filtros.data or []

    materias = safe_execute(supabase.table("materias").select("*")).data or []
    bancas = safe_execute(supabase.table("bancas").select("*")).data or []
    orgaos = safe_execute(supabase.table("orgaos").select("*")).data or []
    escolaridades = safe_execute(supabase.table("niveis_escolaridade").select("*")).data or []
    
    cargos = safe_execute(supabase.table("cargos").select("*")).data or []
    for o in orgaos:
        o['cargos'] = [c for c in cargos if c.get('id_orgao') == o['id_orgao']]
    
    anos_disponiveis = [str(a) for a in range(2026, 1999, -1)]
    
    pagina_atual = int(request.args.get('page', 1))
    itens_por_pagina = 10
    inicio = (pagina_atual - 1) * itens_por_pagina
    fim = inicio + itens_por_pagina - 1

    f_id_questao = request.args.get('id_questao')
    f_status = request.args.get('status', 'todas')
    f_materias = request.args.getlist('id_materia')
    f_topicos = request.args.getlist('id_topico')
    f_subtopicos = request.args.getlist('id_subtopico')
    f_bancas = request.args.getlist('id_banca')
    f_orgaos = request.args.getlist('id_orgao')
    f_anos = request.args.getlist('ano')
    f_nivel = request.args.get('id_nivel')
    f_cargos = request.args.getlist('id_cargo')
    f_tipos = request.args.getlist('tipo_questao')

    current_materia = None
    current_topico = None

    if materia_slug:
        target_m = next((m for m in materias if slugify(m['nome_materia']) == materia_slug), None)
        if target_m:
            mid = str(target_m['id_materia'])
            if mid not in f_materias: f_materias.append(mid)
            current_materia = target_m
            
            if topico_slug:
                topicos_m = safe_execute(supabase.table("topicos").select("*").eq("id_materia", target_m['id_materia'])).data or []
                target_t = next((t for t in topicos_m if slugify(t['nome_topico']) == topico_slug), None)
                if target_t:
                    tid = str(target_t['id_topico'])
                    if tid not in f_topicos: f_topicos.append(tid)
                    current_topico = target_t

    if request.path == url_for('questao.resolver_questoes') and len(f_materias) == 1 and not (f_topicos or f_subtopicos or f_bancas or f_orgaos or f_anos or f_nivel or f_cargos or f_tipos):
        target_m = next((m for m in materias if str(m['id_materia']) == f_materias[0]), None)
        if target_m:
            return redirect(url_for('questao.resolver_questoes', materia_slug=slugify(target_m['nome_materia'])), code=301)

    historico_data = []
    if current_user.is_authenticated:
        query_hist = supabase.table("historico_respostas") \
            .select("id_questao, is_correct") \
            .eq("id_usuario", current_user.id) \
            .limit(50000)
        
        res_historico = safe_execute(query_hist)
        historico_data = res_historico.data if res_historico.data else []

    ids_respondidos = [item['id_questao'] for item in historico_data]
    ids_acertos = [item['id_questao'] for item in historico_data if item.get('is_correct') is True]
    ids_erros = [item['id_questao'] for item in historico_data if item.get('is_correct') is False]

    query = supabase.table("view_questoes_completa").select("*", count=CountMethod.exact).eq("status", "publicada")

    if f_status == 'nao_respondidas' and ids_respondidos:
        query = query.not_.in_('id_questao', ids_respondidos)
    elif f_status == 'respondidas':
        if ids_respondidos: query = query.in_('id_questao', ids_respondidos)
        else: query = query.eq('id_questao', 0)
    elif f_status == 'acertos':
        if ids_acertos: query = query.in_('id_questao', ids_acertos)
        else: query = query.eq('id_questao', 0)
    elif f_status == 'erros':
        if ids_erros: query = query.in_('id_questao', ids_erros)
        else: query = query.eq('id_questao', 0)

    if f_id_questao and f_id_questao.isdigit(): query = query.eq('id_questao', int(f_id_questao))
    if f_materias: query = query.in_('id_materia', f_materias)
    if f_topicos: query = query.in_('id_topico', f_topicos)
    if f_subtopicos: query = query.in_('id_subtopico', f_subtopicos)
    if f_bancas: query = query.in_('id_banca', f_bancas)
    if f_orgaos: query = query.in_('id_orgao', f_orgaos)
    if f_anos: query = query.in_('ano', f_anos)
    if f_nivel: query = query.eq('id_nivel', f_nivel)
    if f_cargos: query = query.in_('id_cargo', f_cargos)
    if f_tipos: query = query.in_('tipo_questao', f_tipos)

    res = safe_execute(query.order('ordem_aleatoria').range(inicio, fim))
    questoes = res.data or []
    total_encontrado = res.count if res.count else 0

    ids_da_pagina = [q['id_questao'] for q in questoes]
    
    contagens = {}
    if ids_da_pagina:
        res_coments = safe_execute(
            supabase.table("comentarios_questao")
            .select("id_questao")
            .in_("id_questao", ids_da_pagina)
        )
        if res_coments.data:
            for c in res_coments.data:
                qid = c['id_questao']
                contagens[qid] = contagens.get(qid, 0) + 1

    for q in questoes:
        query_alt = supabase.table("alternativas_questao").select("*").eq("id_questao", q['id_questao']).order("letra")
        res_alt = safe_execute(query_alt)
        q['alternativas_questao'] = res_alt.data or []
        q['total_comentarios'] = contagens.get(q['id_questao'], 0)

    if ids_da_pagina:
        res_taxas = safe_execute(
            supabase.table("view_taxa_acerto_questoes")
            .select("id_questao, taxa_acerto")
            .in_("id_questao", ids_da_pagina)
        )
        taxas_map = {t['id_questao']: t['taxa_acerto'] for t in (res_taxas.data or [])}
        for q in questoes:
            q['taxa_acerto'] = taxas_map.get(q['id_questao'])

    tem_proxima = total_encontrado > (pagina_atual * itens_por_pagina)
    tem_anterior = pagina_atual > 1

    is_premium = True  # Software livre: acesso liberado para autenticados

    return render_template('questoes/resolver.html',
                           questoes=questoes,
                           total_encontrado=total_encontrado,
                           pagina_atual=pagina_atual, 
                           tem_proxima=tem_proxima, 
                           tem_anterior=tem_anterior,
                           materias=materias, 
                           bancas=bancas, 
                           orgaos=orgaos, 
                           escolaridades=escolaridades, 
                           anos=anos_disponiveis,
                           f_status=f_status,
                           ids_acertos=ids_acertos,
                           ids_erros=ids_erros,
                           filtros_salvos=filtros_salvos,
                           is_premium=is_premium,
                           current_materia=current_materia,
                           current_topico=current_topico)


@questao_bp.route('/questoes/<materia_slug>/<topico_slug>/q<int:id_questao>')
@questao_bp.route('/questoes/<materia_slug>/q<int:id_questao>', defaults={'topico_slug': None})
@limiter.exempt
def visualizar_questao_seo(materia_slug, topico_slug, id_questao):
    query = supabase.table("view_questoes_completa").select("*").eq("id_questao", id_questao).single()
    res = safe_execute(query)
    
    if not res.data:
        abort(404)
    
    questao = res.data
    real_materia_slug = slugify(questao.get('nome_materia', 'geral'))
    real_topico_slug = slugify(questao.get('nome_topico', 'assunto'))
    
    if materia_slug != real_materia_slug or (topico_slug and topico_slug != real_topico_slug):
        return redirect(url_for('questao.visualizar_questao_seo', 
                                materia_slug=real_materia_slug, 
                                topico_slug=real_topico_slug, 
                                id_questao=id_questao), code=301)

    res_alt = safe_execute(supabase.table("alternativas_questao").select("*").eq("id_questao", id_questao).order("letra"))
    questao['alternativas_questao'] = res_alt.data or []
    
    res_coments = safe_execute(supabase.table("comentarios_questao").select("id_questao", count=CountMethod.exact).eq("id_questao", id_questao))
    questao['total_comentarios'] = res_coments.count if res_coments.count else 0

    res_taxa = safe_execute(supabase.table("view_taxa_acerto_questoes").select("taxa_acerto").eq("id_questao", id_questao).maybe_single())
    if res_taxa and res_taxa.data:
        questao['taxa_acerto'] = res_taxa.data.get('taxa_acerto')

    ids_acertos = []
    ids_erros = []
    limit_reached = False

    if current_user.is_authenticated:
        res_hist = safe_execute(supabase.table("historico_respostas").select("id_questao, is_correct").eq("id_usuario", current_user.id).eq("id_questao", id_questao))
        if res_hist.data:
            if any(h['is_correct'] for h in res_hist.data):
                ids_acertos.append(id_questao)
            else:
                ids_erros.append(id_questao)
    else:
        from utils import verificar_bot_real
        is_bot = verificar_bot_real(request.remote_addr, request.user_agent.string)

        from flask import session
        if 'anon_questoes' not in session:
            session['anon_questoes'] = []
            
        questoes_vistas = list(set(int(x) for x in session.get('anon_questoes', []) if str(x).isdigit()))
        
        if id_questao not in questoes_vistas:
            if not is_bot and len(questoes_vistas) >= 5:
                limit_reached = True
            else:
                if not is_bot:
                    questoes_vistas.append(id_questao)
                    session['anon_questoes'] = questoes_vistas
                    session.modified = True

    is_premium = True  # Software livre: acesso liberado para autenticados

    return render_template('questoes/visualizar_individual.html', 
                           q=questao,
                           ids_acertos=ids_acertos,
                           ids_erros=ids_erros,
                           is_premium=is_premium,
                           limit_reached=limit_reached)


@questao_bp.route('/api/responder', methods=['POST'])
@aluno_required
@limiter.exempt
def salvar_resposta():
    data = request.json
    id_questao = data.get('id_questao')
    id_alternativa = data.get('id_alternativa')
    is_correct = data.get('is_correct')

    query_historico = supabase.table("historico_respostas").insert({
        "id_usuario": current_user.id,
        "id_questao": id_questao,
        "id_alternativa_marcada": id_alternativa,
        "is_correct": is_correct
    })

    try:
        safe_execute(query_historico)
        return jsonify({"success": True})
    except Exception as e:
        print(f"❌ Erro definitivo ao salvar histórico: {e}")
        return jsonify({"success": False, "error": "Erro ao salvar seu progresso."}), 500


@questao_bp.route('/api/comentarios/<int:id_questao>', methods=['GET'])
@limiter.exempt
def buscar_comentarios(id_questao):
    query_comentarios = supabase.table("comentarios_questao") \
        .select("*") \
        .eq("id_questao", id_questao) \
        .order("criado_em", desc=True)
    try:
        res = safe_execute(query_comentarios)
        return jsonify(res.data if res.data else [])
    except Exception as e:
        print(f"⚠️ Falha ao buscar comentários (Questão {id_questao}): {e}")
        return jsonify([])


@questao_bp.route('/api/comentarios', methods=['POST'])
@limiter.exempt
@aluno_required
def salvar_comentario():
    dados = request.get_json()
    id_questao = dados.get('id_questao')
    texto = dados.get('texto')

    from utils import verificar_texto_improprio
    sucesso_mod, msg_erro = verificar_texto_improprio(texto)
    if not sucesso_mod:
        return jsonify({"success": False, "error": msg_erro}), 400

    try:
        query_user = supabase.table("usuarios")\
            .select("username")\
            .eq("id", current_user.id)\
            .single()
        
        res_user = safe_execute(query_user)
        nome_aluno = res_user.data.get("username") if res_user.data else "Concurseiro"

        query_insert = supabase.table("comentarios_questao").insert({
            "id_questao": id_questao,
            "id_usuario": str(current_user.id),
            "nome_usuario": nome_aluno,
            "texto_comentario": texto
        })
        safe_execute(query_insert)
        return jsonify({"success": True})
    except Exception as e:
        print(f"❌ Erro crítico ao salvar comentário: {e}")
        if current_app.config.get('TESTING'):
            raise e
        return jsonify({"success": False, "error": "Não foi possível enviar seu comentário agora."}), 500


@questao_bp.route('/api/feedback', methods=['POST'])
@aluno_required
@limiter.exempt
def salvar_feedback():
    dados = request.get_json()
    tipo = dados.get('tipo_erro', 'Não informado')
    texto_digitado = dados.get('descricao', '')
    id_questao = dados.get('id_questao')
    
    relato_completo = f"[{tipo}] {texto_digitado}"
    query_feedback = supabase.table("feedbacks_questoes").insert({
        "id_questao": id_questao,
        "relato": relato_completo
    })
    try:
        safe_execute(query_feedback)
        return jsonify({"success": True})
    except Exception as e:
        print(f"❌ Erro ao salvar feedback da questão {id_questao}: {e}")
        return jsonify({"success": False, "error": "Não foi possível enviar o feedback no momento."}), 500


def sanitizar_latex(texto):
    return texto


@questao_bp.route('/api/ia_explica', methods=['POST'])
@limiter.exempt
@aluno_required
@premium_required
def ia_explica():
    if not client_gpt:
        return jsonify({"explicacao": "IA não configurada."}), 500

    dados = request.json
    id_q = dados.get('id_questao')

    try:
        res_cache = safe_execute(supabase.table("explicacoes_ia").select("conteudo_explicacao").eq("id_questao", id_q))
        if res_cache.data:
            return jsonify({"explicacao": res_cache.data[0]['conteudo_explicacao']})

        res_q = safe_execute(supabase.table("questoes").select("*, textos_base(conteudo_texto)").eq("id_questao", id_q).single())
        q = res_q.data
        if not q:
            return jsonify({"explicacao": "Questão não encontrada."}), 404

        res_alt = safe_execute(supabase.table("alternativas_questao").select("*").eq("id_questao", id_q).order("letra"))
        alts = res_alt.data or []

        system_prompt = (
            "Você é um professor especialista em concursos públicos no Brasil. Sua função é explicar o gabarito de questões objetivas de forma pedagógica, clara e direta.\n\n"
            "REGRAS ESTRITAS:\n"
            "NÃO INVENTE LEIS: Baseie-se exclusivamente em legislação, doutrina e jurisprudência reais e vigentes. Se não tiver certeza absoluta sobre o embasamento legal, não deduza.\n"
            "SEJA PEDAGÓGICO: Não se limite a parafrasear ou resumir o enunciado. Explique objetivamente o erro de cada alternativa incorreta e o acerto da correta.\n"
            "PRECISÃO DE ABRANGÊNCIA: Respeite a hierarquia e o escopo das leis. Diferencie estritamente leis de abrangência estadual (como a Lei Estadual nº 12.209/2011 da Bahia) de matérias e princípios de abrangência nacional.\n"
            "VERIFICAÇÃO LEGISLATIVA: Se identificar que a questão está baseada em lei revogada ou alterada, adicione OBRIGATORIAMENTE uma seção '### ⚖️ Alerta de Desatualização Legislativa' no início da resposta, explicando o que mudou.\n"
            "FORMATO: Retorne a resposta estruturada em tópicos curtos, analisando alternativa por alternativa (A, B, C, D, E).\n\n"
            "ESTRUTURA OBRIGATÓRIA (Use Markdown):\n"
            "### 📌 Tema da Questão\n"
            "• **Assunto**: [Breve explicação do que a questão trata].\n\n"
            "### 🧠 Resolução Comentada\n"
            "[Explicação fluida e direta da resolução. Use parágrafos contínuos. NÃO use blockquotes ('>').]\n\n"
            "### ✅ Alternativa Correta\n"
            "• **Letra [L]**: [Por que esta opção é a correta?].\n\n"
            "### ❌ Alternativas Incorretas\n"
            "• **Letra [X]**: [Por que está incorreta].\n"
            "• **Letra [Y]**: [Por que está incorreta].\n\n"
            "### ⚠️ Pegadinha da Banca\n"
            "[Aponte o que poderia induzir o aluno ao erro nesta questão específica.]\n\n"
            "REGRAS DE ESTILO E SEGURANÇA:\n"
            "1. PROIBIDO usar '>' ou '|' no início das linhas. Use parágrafos normais ou bullet points (•).\n"
            "2. Estilo de parágrafo: Escreva de forma contínua. Evite listas numeradas longas se puder explicar em um parágrafo robusto.\n"
            "3. **Matemática (LaTeX)**: Regras CRÍTICAS:\n"
            "   - Use $ ... $ para fórmulas no meio do texto (inline).\n"
            "   - Use $$ ... $$ para fórmulas destacadas (bloco).\n"
            "   - NUNCA escreva frações ou contas sem usar os símbolos $.\n"
            "   - Palavras dentro de fórmulas DEVEM usar \\text{...} (ex: $$ P(\\text{consoante}) = \\frac{3}{4} $$). Isso é obrigatório para ficar legível.\n"
            "4. **Valores Monetários**: Use 'R$ 10,00' normalmente. O sistema protegerá o símbolo do Real.\n"
            "5. Destaque termos técnicos usando tags HTML <b>...</b> (ex: <b>Termo Técnico</b>). PROIBIDO usar asteriscos (**) para negrito.\n"
            "6. Se a questão tiver fórmulas, explique o passo a passo matemático usando LaTeX impecável.\n"
            "7. Mantenha o tom profissional e encorajador.\n"
            "8. PROIBIDO usar qualquer formatação Markdown como #, **, __, etc.\n"
            "9. **Nomes com Underscore**: Para nomes de atributos ou tabelas com underscore (ex: Nome_RazaoSocial), escreva-os OBRIGATORIAMENTE dentro de \\text{...} se estiver em fórmula LaTeX, ou dentro de blocos de código (ex: `Nome_RazaoSocial`) se estiver no texto comum. Nunca deixe o underscore solto para evitar conflitos de Markdown."
        )

        gabarito_letra = next((a['letra'] for a in alts if a['is_correct']), "?")
        prompt_usuario = f"Explique pedagogicamente esta questão.\nQuestão: {q['enunciado']}\n"
        prompt_usuario += "Alternativas:\n"
        for a in alts:
            texto_alt = a.get('texto') or a.get('texto_alternativa') or "N/A"
            prompt_usuario += f"{a['letra']}) {texto_alt}\n"
        prompt_usuario += f"\nGabarito Correto: {gabarito_letra}\n"
        if q.get('textos_base'):
            prompt_usuario += f"Texto base de apoio (Lei seca): {q['textos_base']['conteudo_texto']}\n"

        import re
        urls_imagens = []
        
        if q.get('url_imagem'):
            try:
                # Bucket público: URL direta (a policy SELECT do storage foi
                # removida na migration rls_header_app_aluno — signed URL desnecessário)
                urls_imagens.append(supabase.storage.from_("imagens_questoes").get_public_url(q['url_imagem'].split('/')[-1]))
            except Exception as e:
                print(f"⚠️ Erro ao gerar URL pública da imagem (Legado): {e}")

        if q.get('enunciado'):
            urls_imagens.extend(re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', q['enunciado']))
        for a in alts:
            texto_alt = a.get('texto') or a.get('texto_alternativa') or ""
            urls_imagens.extend(re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', texto_alt))

        conteudo_gpt: list[dict[str, Any]] = [{"type": "text", "text": prompt_usuario}]
        for url in urls_imagens:
            conteudo_gpt.append({"type": "image_url", "image_url": {"url": url}})

        response = client_gpt.chat.completions.create(  # type: ignore[no-matching-overload]
            model=MODELO_GPT,
            messages=[
                {"role": "developer", "content": system_prompt},
                {"role": "user", "content": conteudo_gpt}  # type: ignore[arg-type]
            ],
            temperature=0.0,
            top_p=0.1,
            presence_penalty=0.0,
            frequency_penalty=0.0
        )
        
        explicacao_gerada = response.choices[0].message.content or ""

        import re
        explicacao_final = re.sub(r'(?m)^[ \t]*[>|][ \t]*', r' ', explicacao_gerada)
        explicacao_final = re.sub(r' +', r' ', explicacao_final)

        safe_execute(supabase.table("explicacoes_ia").insert({"id_questao": id_q, "conteudo_explicacao": explicacao_final}))

        return jsonify({"explicacao": explicacao_final})
    except Exception as e:
        print(f"❌ ERRO IA: {e}")
        return jsonify({"explicacao": "Erro ao gerar explicação. Tente novamente."}), 500


@questao_bp.route('/api/ia/gerar_estudo', methods=['POST'])
@limiter.exempt
@aluno_required
@premium_required
def ia_gerar_estudo():
    if not client_gpt:
        return jsonify({"success": False, "error": "IA não configurada."}), 500

    dados = request.json
    id_q = dados.get('id_questao')
    tipo = dados.get('tipo')

    if not id_q or not tipo:
        return jsonify({"success": False, "error": "Dados incompletos."}), 400

    try:
        res_q = safe_execute(
            supabase.table("view_questoes_completa")
            .select("*")
            .eq("id_questao", id_q)
            .single()
        )
        q = res_q.data
        if not q:
            return jsonify({"success": False, "error": "Questão não encontrada."}), 404

        user_id = str(current_user.id)

        if tipo == 'resumo':
            res_check = safe_execute(supabase.table("resumos_estudo").select("id_resumo").eq("id_usuario", user_id).eq("id_questao", id_q).maybe_single())
            if res_check and res_check.data:
                return jsonify({
                    "success": True, 
                    "mensagem": "Este resumo já está no seu caderno!",
                    "cache": True
                })
        else:
            res_check = safe_execute(supabase.table("flashcards").select("id_flashcard").eq("id_usuario", user_id).eq("id_questao", id_q).maybe_single())
            if res_check and res_check.data:
                return jsonify({
                    "success": True, 
                    "mensagem": "Você já possui um flashcard para esta questão!",
                    "cache": True
                })

        res_global = safe_execute(
            supabase.table("ia_cache_estudo")
            .select("conteudo_json")
            .eq("id_questao", id_q)
            .eq("tipo", tipo)
            .maybe_single()
        )
        
        cache_hit = False
        conteudo_ia = None
        
        if res_global and res_global.data:
            conteudo_ia = res_global.data['conteudo_json']
            cache_hit = True
            print(f"✅ CACHE GLOBAL HIT: {tipo} para questão {id_q}")

        res_exp = safe_execute(supabase.table("explicacoes_ia").select("conteudo_explicacao").eq("id_questao", id_q))
        explicacao_base = res_exp.data[0]['conteudo_explicacao'] if res_exp.data else ""

        res_alt = safe_execute(supabase.table("alternativas_questao").select("*").eq("id_questao", id_q).order("letra"))
        alts = res_alt.data or []
        gabarito = next((a['letra'] for a in alts if a['is_correct']), "?")
        
        id_mat = q.get('id_materia')
        nome_mat = q.get('nome_materia') or "Geral"
        template_materia = "Você é um professor especialista concursado."
        if id_mat:
            res_p = safe_execute(supabase.table("prompts_materias").select("template_prompt").eq("id_materia", id_mat))
            if res_p.data:
                template_materia = res_p.data[0]['template_prompt']

        if tipo == 'resumo':
            system_prompt = (
                f"{template_materia}\n"
                "Sua tarefa é criar um RESUMO TEÓRICO sobre o ASSUNTO da questão para um Caderno de Estudos.\n\n"
                "O objetivo é que o aluno aprenda a TEORIA por trás da questão, e não a resolução da questão in si.\n\n"
                "ESTRUTURA OBRIGATÓRIA (Markdown):\n"
                "### 📌 [Título do Assunto/Tema]\n"
                "• **Conceito Central**: Explicação objetiva e tecnicamente precisa do núcleo do tema, com linguagem de concurso.\n"
                "• **Regras e Detalhes**: Pontos teóricos relevantes, específicos e frequentemente cobrados em prova.\n"
                "⚠️ **Cuidado com a Pegadinha**: Aponte erro comum de prova, distinção relevante ou confusão clássica entre institutos.\n\n"
                "💡 *Fixação: Uma frase curta e memorável com o ponto mais importante.*\n\n"
                "PROIBIÇÕES ESTRITAS:\n"
                "- NÃO mencione alternativas (A, B, C, D, E).\n"
                "- NÃO explique por que uma opção está certa ou errada.\n"
                "- NÃO use frases como 'A questão pede', 'O gabarito é', 'Nesta questão'.\n"
                "- O texto deve ser um material de estudo independente da questão original.\n\n"
                "REGRAS DE ESTILO:\n"
                "- Seja conciso e destaque termos técnicos usando exclusivamente tags HTML <b>...</b> (ex: <b>Termo Técnico</b>). PROIBIDO usar asteriscos (**).\n"
                "- Evite generalizações vagas; priorize conteúdo específico e útil para provas.\n"
                "- Cada seção deve conter informações suficientes para revisão.\n"
                "- Linguagem técnica de concurso, sem informalidade.\n"
                "- PROIBIDO usar formatação Markdown (#, **, etc.). Use apenas cabeçalhos de nível 3 (###) permitidos na estrutura.\n\n"
                "PRECISÃO E ATUALIZAÇÃO:\n"
                "- Verifique se o assunto da questão sofreu alterações legislativas recentes (ex: Reformas, novas Leis, Súmulas).\n"
                "- Caso o tema esteja desatualizado ou tenha mudado, adicione um destaque: '⚠️ **Nota de Atualização**: [Explique a mudança legislativa recente]'.\n"
                "- Não invente fundamentos legais. Se não tiver certeza, omita.\n"
                "- Priorize exatidão jurídica.\n\n"
                "FORMATAÇÃO:\n"
                "- **Matemática**: Use LaTeX OBRIGATORIAMENTE entre \\( ... \\) ou \\[ ... \\]. NUNCA use cifrão ($). Comandos como \\boxed devem estar dentro dos delimitadores. Use \\\\ para quebras de linha internas em LaTeX.\n\n"
                "CRITÉRIO DE QUALIDADE:\n"
                "A resposta deve ser útil para revisão de prova (nível véspera)."
            )
        else:
            system_prompt = (
                f"{template_materia}\n"
                "Sua tarefa é criar um FLASHCARD (Pergunta e Resposta) para memorização ativa.\n\n"
                "IMPORTANTE: A pergunta deve abordar o conceito teórico central do tema, e não a questão em si.\n\n"
                "ESTRUTURA OBRIGATÓRIA:\n"
                "FRENTE: [Uma pergunta direta, específica e desafiadora]\n"
                "VERSO: [Uma resposta curta, objetiva e fácil de memorizar]\n\n"
                "REGRAS:\n"
                "- Foque na memorização de um único conceito, regra ou exceção.\n"
                "- O card deve ser compreensível por si só, sem depender da questão original.\n"
                "- Proibido perguntar sobre alternativas (A, B, C...) ou comandos da questão.\n\n"
                "QUALIDADE:\n"
                "- A pergunta deve exigir recuperação ativa (evite perguntas genéricas).\n"
                "- Priorize definição, regra, exceção ou distinção entre conceitos.\n"
                "- Sempre que possível, destaque pontos frequentemente cobrados ou confundidos em prova.\n\n"
                "RESPOSTA:\n"
                "- Máximo de 2 linhas.\n"
                "- Estrutura direta e objetiva.\n"
                "- Linguagem técnica de concurso.\n\n"
                "PRECISÃO:\n"
                "- Não invente fundamentos legais.\n"
                "- Priorize exatidão.\n\n"
                "FORMATAÇÃO:\n"
                "- **Matemática**: Use LaTeX OBRIGATORIAMENTE entre \\( ... \\) ou \\[ ... \\]. NUNCA use cifrão ($). NUNCA use [ ou ] fora dos delimitadores LaTeX.\n"
                "- **Destaque**: Use tags HTML <b>...</b> para enfatizar palavras-chave. PROIBIDO usar asteriscos (**).\n"
                "- **Markdown**: PROIBIDO usar qualquer sintaxe Markdown para formatação.\n\n"
                "OBJETIVO FINAL:\n"
                "O flashcard deve ser útil para revisão rápida de prova (nível véspera)."
            )

        if not cache_hit:
            prompt_usuario = (
                f"QUESTÃO: {q['enunciado']}\n"
                f"TEXTO BASE: {q.get('texto_base') or 'N/A'}\n"
                f"GABARITO: {gabarito}\n"
                f"EXPLICAÇÃO PRÉVIA: {explicacao_base}\n"
            )

            import re
            urls_imagens = []
            
            if q.get('url_imagem'):
                try:
                    # Bucket público: URL direta (a policy SELECT do storage foi
                    # removida na migration rls_header_app_aluno — signed URL desnecessário)
                    urls_imagens.append(supabase.storage.from_("imagens_questoes").get_public_url(q['url_imagem'].split('/')[-1]))
                except Exception as e:
                    print(f"⚠️ Erro ao gerar URL pública da imagem (Legado): {e}")

            if q.get('enunciado'):
                urls_imagens.extend(re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', q['enunciado']))
            
            conteudo_gpt: list[dict[str, Any]] = [{"type": "text", "text": prompt_usuario}]
            for url in urls_imagens:
                conteudo_gpt.append({"type": "image_url", "image_url": {"url": url}})

            response = client_gpt.chat.completions.create(  # type: ignore[no-matching-overload]
                model=MODELO_GPT,
                messages=[
                    {"role": "developer", "content": system_prompt},
                    {"role": "user", "content": conteudo_gpt}  # type: ignore[arg-type]
                ],
                temperature=TEMPERATURE_GPT
            )
            conteudo_gerado = response.choices[0].message.content or ""
            
            if tipo == 'resumo':
                conteudo_ia = {"conteudo": conteudo_gerado}
            else:
                f_match = re.search(r"FRENTE:\s*(.*?)(?=\s*VERSO:|$)", conteudo_gerado, re.S | re.I)
                v_match = re.search(r"VERSO:\s*(.*)", conteudo_gerado, re.S | re.I)
                frente_final = f_match.group(1).strip() if f_match else "Revisão: " + nome_mat
                verso_final = v_match.group(1).strip() if v_match else conteudo_gerado
                conteudo_ia = {"frente": frente_final, "verso": verso_final}

            safe_execute(supabase.table("ia_cache_estudo").insert({
                "id_questao": id_q,
                "id_materia": id_mat,
                "tipo": tipo,
                "conteudo_json": conteudo_ia
            }))
            print(f"💾 CACHE GLOBAL SALVO: {tipo} para questão {id_q}")

        user_id = str(current_user.id)

        # Type narrowing: conteudo_ia is guaranteed to be a dict
        conteudo_ia_dict: dict = conteudo_ia  # type: ignore[assignment]

        if tipo == 'resumo':
            safe_execute(supabase.table("resumos_estudo").insert({
                "id_usuario": user_id,
                "id_questao": id_q,
                "id_materia": id_mat,
                "conteudo": conteudo_ia_dict.get('conteudo', '')
            }))
        else:
            res_cat = safe_execute(
                supabase.table("flashcard_categorias")
                .select("id_categoria")
                .eq("id_usuario", user_id)
                .eq("nome_categoria", nome_mat)
            )
            
            if res_cat.data:
                id_cat = res_cat.data[0]['id_categoria']
            else:
                res_new_cat = safe_execute(supabase.table("flashcard_categorias").insert({
                    "id_usuario": user_id,
                    "nome_categoria": nome_mat,
                    "id_materia": id_mat
                }))
                
                if res_new_cat and res_new_cat.data:
                    id_cat = res_new_cat.data[0]['id_categoria']
                else:
                    return jsonify({"success": False, "error": "Falha ao criar categoria automática."}), 500

            safe_execute(supabase.table("flashcards").insert({
                "id_usuario": user_id,
                "id_categoria": id_cat,
                "id_questao": id_q,
                "frente": conteudo_ia['frente'] if conteudo_ia else "Revisão",
                "verso": conteudo_ia['verso'] if conteudo_ia else "..."
            }))

        return jsonify({"success": True, "tipo": tipo})

    except Exception as e:
        print(f"❌ ERRO GERAR ESTUDO IA ({tipo}): {e}")
        return jsonify({"success": False, "error": "Erro ao gerar conteúdo de estudo."}), 500
