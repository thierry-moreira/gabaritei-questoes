# 📚 Módulo de Questões e Inteligência Artificial (`rotas/questao.py`)

Este módulo constitui o núcleo operacional e pedagógico do **Gabaritei**, processando desde a lógica transacional de resolução de questões e controle de ofensivas diárias até o ecossistema generativo da **Gabi IA** (explicações e materiais permanentes de estudo com barramento de cache duplo).

---

## 🛠️ Arquitetura e Funcionalidades Principais

### 1. Resolução e Motor de Ofensiva (Streak)
*   **`responder_questao`**: Rota transacional principal (`/aluno/responder`). Recebe a alternativa marcada, valida contra o banco de dados e registra a atividade no histórico do aluno.
*   **Motor da Ofensiva**: Atualiza de forma resiliente as ofensivas diárias do aluno considerando o fuso horário oficial de Brasília (UTC-3). A lógica matemática da progressão do streak é expressa por:

$$\text{Streak}_{\text{hoje}} = \begin{cases} \text{Streak}_{\text{ontem}} + 1 & \text{se } \text{data}_{\text{última}} = \text{hoje} - 1 \\ 1 & \text{se } \text{data}_{\text{última}} < \text{hoje} - 1 \\ \text{Streak}_{\text{ontem}} & \text{se } \text{data}_{\text{última}} = \text{hoje} \end{cases}$$

*   **`salvar_resposta` (F-08)**: Endpoint de compatibilidade (`POST /api/responder`, sem caller no frontend atual). Continua autenticado e com rate limit de 60/minuto. Valida os IDs e consulta `alternativas_questao` filtrando simultaneamente por `id_questao` e `id_alternativa`; `historico_respostas.is_correct` é sempre copiado do booleano retornado pelo banco — o campo `is_correct` enviado pelo cliente é ignorado. Alternativa não vinculada à questão recebe `400` e não grava histórico.

### 2. Página Pública de Questão (Vitrine SEO)
*   **`visualizar_questao_seo`**: Exibe a página individual da questão (`/questoes/<materia>/q<id>`). Implementa **Redirecionamento Canônico (301)** para corrigir dinamicamente quaisquer slugs corrompidos digitados na URL, garantindo perfeita indexação no Google. É uma vitrine pública: visitantes leem a questão e as alternativas, mas só usuários autenticados respondem — o card substitui o botão de resposta por "Cadastre-se para responder".

### 3. Listagem e Filtros de Questões (`/aluno/questoes`)

*   **`resolver_questoes`**: página principal de resolução, também servida por `/questoes/<materia_slug>` e `/questoes/<materia_slug>/<topico_slug>`. A listagem é pública; quando há sessão, o histórico do aluno alimenta os filtros de status.
*   **Filtro de status**: `f_status = request.args.get('status', 'todas')` — o padrão é **`todas`** (antes era `nao_respondidas`). A sidebar (`templates/components/sidebar_filtros.html`) marca "🔎 Todas as Questões" como selecionada quando o parâmetro está ausente, e "🆕 Apenas Não Respondidas" só fica ativa com `?status=nao_respondidas` explícito.
*   **Valores aceitos**: `todas` (sem filtro), `nao_respondidas` (`NOT IN` nos ids já respondidos), `respondidas`, `acertos` e `erros`. Sem histórico, as três últimas consultas usam `id_questao = 0` para retornar lista vazia em vez de vazar o banco inteiro.
*   **Paginação e ordenação**: 10 questões por página, ordenadas por `ordem_aleatoria`, com contagem exata (`CountMethod.exact`) para calcular `tem_proxima`/`tem_anterior`.
*   **Filtros combinados**: matéria, tópico, subtópico, banca, órgão, ano, nível, cargo e tipo são aplicados via `.in_`/`.eq` sobre a view `view_questoes_completa`, sempre restrita a `status='publicada'`.

### 4. Ecossistema Pedagógico de IA (Gabi IA)
*   **`ia_explica`**: Gera explicações hiper-pedagógicas em tempo real (`/api/ia_explica`) para usuários autenticados, com a **própria chave do aluno (BYOK)**. Integra prompts de sistema altamente restritivos para evitar alucinações de lei, injeta o **contexto legislativo curado** recuperado pela RPC `buscar_legislacao` (RAG leve, com evidência gravada em `explicacoes_ia.contexto_legislacao`) e suporta **visão computacional** enviando as imagens do enunciado/alternativas ao provedor. O cache global é gravado pela Edge Function `secure-global-write` (operação `cache_explanation`); falha no cache não impede a explicação de ser devolvida. Detalhes em [docs/ia.md](../ia.md).
*   **`ia_gerar_estudo`**: Endpoint unificado (`/api/ia/gerar_estudo`) que extrai a teoria subjacente à questão para gerar resumos ou flashcards permanentes:
    *   **Resumos**: Gravados no caderno de resumos do aluno (`resumos_estudo`) e no cache global `ia_cache_estudo`.
    *   **Flashcards**: Pergunta e resposta estruturadas para memorização ativa (Frente/Verso), salvas automaticamente no respectivo baralho da matéria (`flashcards` e `flashcard_categorias`) e no cache global `ia_cache_estudo`.
    *   **Cache global**: gravado pela Edge Function `secure-global-write` (operação `cache_study`), sempre depois de o material do aluno ser salvo; falha no cache (ex.: rate limit) não desfaz o resumo/flashcard.
*   **`feedback_ia`**: Reporte anônimo de problema em qualquer resposta gerada (explicação, resumo ou flashcard) pelo botão 🚩 (`POST /api/feedback_ia`): o motivo é validado contra o catálogo fechado `MOTIVOS_FEEDBACK_IA`, o relato passa pela blocklist local e é enviado à Edge Function `secure-global-write` (operação `feedback_ai`), que valida JWT, questão publicada e rate limit antes de gravar em `feedbacks_ia` com `service_role`. A triagem é humana no painel admin (seção "Respostas da IA"), que pode **invalidar o cache** para o conteúdo ser regerado com o contexto atual.

---

## 📊 Fluxos Operacionais (Diagramas Mermaid)

### Diagrama 1: Ciclo de Resolução e Motor de Ofensiva (Streak)
O diagrama abaixo detalha o fluxo de validação de resposta do aluno, a persistência no histórico de estudos e a execução da lógica de streak no fuso horário UTC-3:

```mermaid
sequenceDiagram
    autonumber
    actor Aluno
    participant App as Flask Route (/aluno/responder)
    participant Limiter as Flask-Limiter
    participant DB as Supabase
    
    Aluno->>App: Responder Questão (questao_id, alternativa)
    App->>Limiter: Verifica Rate Limit (60/min)
    alt Limite Atingido
        Limiter-->>Aluno: Erro 429 (Too Many Requests)
    else Limite OK
        App->>DB: Busca alternativas da questão (alternativas_questao)
        DB-->>App: Lista de alternativas
        App->>App: Valida alternativa marcada e verifica se é correta
        App->>DB: Insere no historico_respostas
        App-->>Aluno: JSON (sucesso, correta, letra_correta, comentario)
    end
```

### Diagrama 2: Arquitetura de IA (Gabi IA) com Barramento de Cache Duplo
Ilustração do ecossistema inteligente que impede redundâncias, implementando cache local no caderno/baralho do aluno e cache global persistido para otimizar custos com APIs e tempo de latência:

```mermaid
graph TD
    A[Aluno] -->|Solicita Explicação / Estudo| B(Flask Route: ia_explica / ia_gerar_estudo)
    B --> E{Tipo de Solicitação?}
    
    %% ia_explica
    E -->|Explicação Pedagógica| F{Existe no Cache Global explicacoes_ia?}
    G[Retorna Explicação do Cache]
    F -->|Não: MISS| H0[Recupera contexto legislativo — RPC buscar_legislacao]
    H0 --> H[Camada BYOK: provedores_ia.chamar_ia]
    H -->|Aplica Prompts e Visão Computacional| I[Sanitiza LaTeX e Tags HTML <b>]
    I -->|Envia cache_explanation + evidência contexto_legislacao| J[Edge secure-global-write → explicacoes_ia]
    J --> G
    
    %% ia_gerar_estudo
    E -->|Gerar Estudo: Resumo/Flashcard| K{Existe no Caderno do Aluno?}
    K -->|Sim: HIT Local| L[Retorna Mensagem de Já Existente no Caderno]
    K -->|Não: MISS Local| M{Existe no Cache Global ia_cache_estudo?}
    
    M -->|Sim: HIT Global| N[Usa Conteúdo em Cache Global e pula a IA]
    M -->|Não: MISS Global| O[Busca Explicação Base + Prompt da Matéria]
    O --> P[Camada BYOK: provedores_ia.chamar_ia]
    P --> Q[Gera JSON / Estrutura Frente-Verso ou Resumo]
    Q -->|Envia cache_study| R[Edge secure-global-write → ia_cache_estudo]
    R --> N
    
    N --> S{Tipo de Estudo?}
    S -->|Resumo| T[Insere na tabela resumos_estudo do Aluno]
    S -->|Flashcard| U[Verifica/Cria Categoria e Insere na tabela flashcards]
    T --> V[Retorna Sucesso e incrementa uso]
    U --> V
```

---

## ⚖️ Diretrizes e Regras do Motor Generativo (BYOK)

O motor generativo adota uma política de **tolerância zero contra alucinações**, além de aplicar formatações rígidas no envio de outputs ao frontend:

### 1. Regras Antialucinação Legislativa
*   **Fundamentação Real**: É expressamente proibido deduzir ou inventar leis, decretos, portarias ou súmulas jurídicas. Se não houver certeza doutrinária ou legal, o motor silencia a dedução.
*   **Grounding por Contexto Curado (RAG leve)**: além das regras do prompt, a geração recebe os dispositivos legais recuperados do corpus curado (`legislacao.py` → RPC `buscar_legislacao`) e deve citar apenas dispositivos transcritos nesse contexto; a evidência usada é gravada em `explicacoes_ia.contexto_legislacao` para auditoria. Sem contexto disponível, o fluxo segue normalmente (fail-open).
*   **Precisão Territorial**: O motor respeita de forma rígida a abrangência territorial da lei seca (e.g. diferenciando uma lei municipal ou estadual de normas nacionais como a Lei nº 8.112/1990).
*   **Alerta de Desatualização**: Caso o enunciado trate de matéria revogada, o sistema gera obrigatoriamente um bloco de alerta técnico:

> [!WARNING]
> ### ⚖️ Alerta de Desatualização Legislativa
> [Explicação sucinta sobre a nova norma ou alteração na jurisprudência.]

### 2. Normas Estritas de Formatação (LaTeX e HTML)
*   **Destaque Visual**: É proibido o uso de asteriscos para negrito (`**`). Todos os termos técnicos devem ser enfatizados utilizando as tags HTML `<b>` e `</b>` (e.g. `<b>Princípio da Legalidade</b>`).
*   **Renderização KaTeX/LaTeX**: 
    *   *Explicações*: Uso obrigatório de $ ... $ para delimitadores matemáticos no corpo de texto (inline) e $$ ... $$ para fórmulas em bloco separado.
    *   *Resumos/Flashcards*: Uso obrigatório de delimitadores curtos `\( ... \)` para inline e `\[ ... \]` para destaque em bloco.
    *   *Fórmulas*: Toda notação fracionária ou complexa deve ser expressa por equações formais em LaTeX (e.g. `\( \frac{a}{b} \)`), garantindo renderização limpa no frontend.
*   **Prevenção Anti-Layout**:
    *   Remoção automática por Expressão Regular no back-end de quaisquer caracteres de citação (`>` ou `|`) no início das linhas, impedindo a injeção indesejada de barras de blockquotes que quebram o design responsivo.
    *   Tratamento estrito de underscores (`_`) em variáveis ou atributos (e.g. `Nome_RazaoSocial`), envolvendo-os sempre em blocos de código (\`...\`) ou tags de texto LaTeX (`\text{...}`) para não corromper o interpretador de Markdown.

---

## 🔐 Segurança, IDOR e Integridade de Dados

*   **Proteção Contra IDOR**:
    *   A deleção física de questões (`excluir_questao`) migrou para o ambiente administrativo (`rotas/admin_api.py`, blindada por `@admin_required` com trava de dispositivo único — ver `docs/rotas/admin.md` no repositório do painel administrativo). O blueprint de questões do aluno não expõe nenhuma rota destrutiva.
    *   A inserção de resumos e flashcards sempre resolve e força a propriedade ao UUID autenticado do aluno (`current_user.id`), inviabilizando qualquer injeção ou tentativa de alteração cruzada de dados por IDs arbitrários.
*   **Feedback de questões**: o relato de problema na questão (modal do formulário de feedback → `POST /api/feedback`) valida `id_questao`, o catálogo fechado de `tipo_erro` e o tamanho da descrição, e envia a gravação à Edge Function `secure-global-write` (operação `feedback_question`). A função confirma aluno, questão publicada e rate limit (10/hora) antes de inserir em `feedbacks_questoes` com `service_role`, no formato `"[tipo] descrição"`, para triagem humana no painel admin. `anon`/`authenticated` não têm INSERT direto na tabela.
*   **Feed público de comentários (F-07)**: `GET /api/comentarios/<id_questao>` consulta somente `view_comentarios_publicos` e seleciona/projeta `id_comentario`, `nome_usuario`, `texto_comentario` e `criado_em` — nunca `id_usuario`. A rota limita a **20 comentários por página**, ordena por data e UUID para paginação estável, busca um registro extra para retornar `tem_mais`, rejeita páginas inválidas e limita o offset a 10.000. A interface oferece “Carregar comentários anteriores”; o endpoint tem rate limit de **60/minuto** por IP. Não exige login; a view do F-01 filtra para questões publicadas.
*   **Moderação sem IA (blocklist + denúncia humana)**: o salvamento de novos comentários passa pela blocklist local (`verificar_texto_improprio`) — a antiga moderação por API de IA foi removida. A segunda barreira é a **denúncia** (`POST /api/comentarios/<id_comentario>/reportar`, botão 🚩 em cada comentário): grava em `reports_comentarios` (no máximo 1 por comentário/aluno → `409` duplicado amigável; uuid validado; comentário inexistente → `404`) e a triagem é **humana**, no painel do admin (repo separado) — seção "Denúncias de Comentários" da página de feedbacks, com exclusão do comentário denunciado (FK CASCADE encerra as denúncias) ou descarte da denúncia.
*   **XSS armazenado em comentários (F-11)**: `salvar_comentario` valida `id_questao` inteiro e o texto com `utils.validar_texto_comentario` (1–1000 caracteres, sem controles) antes de consultar o banco; o `username` do perfil passa por `utils.validar_username` e um valor legado fora do formato vira `"Concurseiro"`. A defesa principal é na saída: `static/js/questoes_common.js` monta o card com `createElement`/`textContent`/`createTextNode` — nome, texto e id nunca são interpolados em `innerHTML`. No banco, as CHECKs `usuarios_username_formato`, `comentarios_nome_usuario_formato` e `comentarios_texto_valido` (migration `comentarios_username_xss`) bloqueiam INSERT direto via PostgREST com HTML, texto vazio/longo ou caractere de controle (`23514`). O CSP mantém `'unsafe-inline'` em `script-src` por causa dos scripts inline legados; `object-src 'none'`, `base-uri 'self'`, `frame-ancestors 'self'` e `form-action 'self'` foram adicionados. Testes: `tests/test_utils.py`, `tests/test_aluno_questoes.py`, `tests/test_conta.py`, `tests/test_auth.py`, `tests/test_app_security.py` (CSP), `static/js/__tests__/questoes_common.test.js` e `docs/migrations/test_f11.sql` (8 asserções).
*   **IA com BYOK**: `/api/ia_explica` e `/api/ia/gerar_estudo` chamam a camada `provedores_ia.chamar_ia()` com a **própria chave do aluno** (OpenAI, Google Gemini ou Anthropic), guardada apenas localmente (SQLite + DPAPI). Os prompts e parâmetros calibrados permanecem idênticos; a gravação dos caches globais (`explicacoes_ia`, `ia_cache_estudo`) passa pela Edge Function `secure-global-write`, com falha degradada (o conteúdo gerado é entregue mesmo sem cache). Detalhes em [docs/ia.md](../ia.md).

---
> [!NOTE]
> **Tabelas de Cache Operacionais**:
> *   `explicacoes_ia`: Armazena explicações brutas associadas a cada ID de questão.
> *   `ia_cache_estudo`: Centraliza em JSON os resumos e flashcards categorizados gerados por IA, eliminando requisições repetidas de OpenAI para a mesma questão acadêmica no ecossistema global.
