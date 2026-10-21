# 📚 Módulo de Questões e Inteligência Artificial (`rotas/questao.py`)

Este módulo constitui o núcleo operacional e pedagógico do **Gabaritei**, processando desde a lógica transacional de resolução de questões e controle de ofensivas diárias até o ecossistema generativo da **Gabi IA** (explicações e materiais permanentes de estudo com barramento de cache duplo).

---

## 🛠️ Arquitetura e Funcionalidades Principais

### 1. Resolução e Motor de Ofensiva (Streak)
*   **`responder_questao`**: Rota transacional principal (`/aluno/responder`). Recebe a alternativa marcada, valida contra o banco de dados e registra a atividade no histórico do aluno.
*   **Motor da Ofensiva**: Atualiza de forma resiliente as ofensivas diárias do aluno considerando o fuso horário oficial de Brasília (UTC-3). A lógica matemática da progressão do streak é expressa por:

$$\text{Streak}_{\text{hoje}} = \begin{cases} \text{Streak}_{\text{ontem}} + 1 & \text{se } \text{data}_{\text{última}} = \text{hoje} - 1 \\ 1 & \text{se } \text{data}_{\text{última}} < \text{hoje} - 1 \\ \text{Streak}_{\text{ontem}} & \text{se } \text{data}_{\text{última}} = \text{hoje} \end{cases}$$

*   **`salvar_resposta`**: Endpoint da API pública para persistência síncrona com verificação de cotas de resolução diária para usuários do plano gratuito.

### 2. Paywall e Indexação Otimizada (SEO)
*   **`responder_publico`**: Endpoint com rate limit especial (`/api/responder_publico`) para tráfego anônimo (Landing Page). Permite que visitantes respondam a até **5 questões por sessão**, salvando os IDs na sessão do Flask (`anon_questoes`) para conversão.
*   **`visualizar_questao_seo`**: Exibe a página individual da questão (`/questoes/<materia>/q<id>`). Implementa **Redirecionamento Canônico (301)** para corrigir dinamicamente quaisquer slugs corrompidos digitados na URL, garantindo perfeita indexação no Google.
*   **Isenção de Crawlers**: Utiliza verificação de DNS reverso e análise de cabeçalhos de User-Agent no utilitário `verificar_bot_real` para isentar bots oficiais de busca (Googlebot/Bingbot) do bloqueio do paywall, mantendo 100% da biblioteca de questões indexada para SEO.

### 3. Ecossistema Pedagógico de IA (Gabi IA)
*   **`ia_explica`**: Gera explicações hiper-pedagógicas em tempo real (`/api/ia_explica`) para usuários Premium. Integra prompts de sistema altamente restritivos para evitar alucinações de lei e suporta **visão computacional** enviando imagens extraídas do enunciado/alternativas via URLs assinadas e seguras à API do GPT-4o mini.
*   **`ia_gerar_estudo`**: Endpoint unificado (`/api/ia/gerar_estudo`) que extrai a teoria subjacente à questão para gerar resumos ou flashcards permanentes:
    *   **Resumos**: Gravados no caderno de resumos do aluno (`resumos_estudo`).
    *   **Flashcards**: Pergunta e resposta estruturadas para memorização ativa (Frente/Verso), salvas automaticamente no respectivo baralho da matéria (`flashcards` e `flashcard_categorias`).

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

### Diagrama 2: Paywall SEO e Isenção de Robôs de Busca Real
Este diagrama ilustra a proteção de tráfego, separando a verificação estrita de paywall (limite de 5 questões para visitantes) da isenção total oferecida a robôs reais para maximizar a indexação SEO:

```mermaid
sequenceDiagram
    autonumber
    actor Visitante as Usuário Anônimo / Crawler
    participant App as Flask Route (/questoes/... ou /responder_publico)
    participant Util as verificar_bot_real (Reverse DNS)
    participant Session as Flask Session (anon_questoes)
    participant DB as Supabase
    
    Visitante->>App: Acessa Questão SEO / Envia resposta pública
    App->>Util: verificar_bot_real(IP, User-Agent)
    Util-->>App: Retorna is_bot (True/False)
    
    alt É Robô de Busca Real (Googlebot/Bingbot)
        Note over App: Isenção Total de Paywall
        App->>DB: Busca dados da questão
        DB-->>App: Dados
        App-->>Visitante: Renderiza página completa (SEO indexável)
    else É Usuário Comum
        App->>Session: Recupera 'anon_questoes' da sessão
        Session-->>App: Lista de IDs de questões vistas
        
        alt IDs vistos >= 5 e questão atual não está na lista
            App-->>Visitante: Exibe Paywall / Bloqueia resolução (Erro 403)
        else Permissão concedida
            alt Questão atual não vista
                App->>Session: Adiciona ID à lista 'anon_questoes'
                App->>DB: Insere em historico_respostas_anonimo (para estatística)
            end
            App->>DB: Busca dados da questão
            DB-->>App: Dados
            App-->>Visitante: Exibe Questão / Retorna resultado
        end
    end
```

### Diagrama 3: Arquitetura de IA (Gabi IA) com Barramento de Cache Duplo
Ilustração do ecossistema inteligente que impede redundâncias, implementando cache local no caderno/baralho do aluno e cache global persistido para otimizar custos com APIs e tempo de latência:

```mermaid
graph TD
    A[Aluno] -->|Solicita Explicação / Estudo| B(Flask Route: ia_explica / ia_gerar_estudo)
    B --> E{Tipo de Solicitação?}
    
    %% ia_explica
    E -->|Explicação Pedagógica| F{Existe no Cache Global explicacoes_ia?}
    G[Retorna Explicação do Cache]
    F -->|Não: MISS| H[Chama OpenAI GPT-4o mini]
    H -->|Aplica Prompts e Visão Computacional| I[Sanitiza LaTeX e Tags HTML <b>]
    I -->|Salva Cache Global| J[(Tabela: explicacoes_ia)]
    J --> G
    
    %% ia_gerar_estudo
    E -->|Gerar Estudo: Resumo/Flashcard| K{Existe no Caderno do Aluno?}
    K -->|Sim: HIT Local| L[Retorna Mensagem de Já Existente no Caderno]
    K -->|Não: MISS Local| M{Existe no Cache Global ia_cache_estudo?}
    
    M -->|Sim: HIT Global| N[Usa Conteúdo em Cache Global e pula OpenAI]
    M -->|Não: MISS Global| O[Busca Explicação Base + Prompt da Matéria]
    O --> P[Chama OpenAI GPT-4o mini]
    P --> Q[Gera JSON / Estrutura Frente-Verso ou Resumo]
    Q -->|Salva Cache Global| R[(Tabela: ia_cache_estudo)]
    R --> N
    
    N --> S{Tipo de Estudo?}
    S -->|Resumo| T[Insere na tabela resumos_estudo do Aluno]
    S -->|Flashcard| U[Verifica/Cria Categoria e Insere na tabela flashcards]
    T --> V[Retorna Sucesso e incrementa uso]
    U --> V
```

---

## ⚖️ Diretrizes e Regras do Motor Generativo (GPT-4o mini)

O motor generativo adota uma política de **tolerância zero contra alucinações**, além de aplicar formatações rígidas no envio de outputs ao frontend:

### 1. Regras Antialucinação Legislativa
*   **Fundamentação Real**: É expressamente proibido deduzir ou inventar leis, decretos, portarias ou súmulas jurídicas. Se não houver certeza doutrinária ou legal, o motor silencia a dedução.
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
    *   A deleção física de questões (`excluir_questao`) migrou para o ambiente administrativo (`rotas/admin_api.py`, blindada por `@admin_required` com trava de dispositivo único — ver `docs/rotas/admin.md`). O blueprint de questões do aluno não expõe nenhuma rota destrutiva.
    *   A inserção de resumos e flashcards sempre resolve e força a propriedade ao UUID autenticado do aluno (`current_user.id`), inviabilizando qualquer injeção ou tentativa de alteração cruzada de dados por IDs arbitrários.
*   **Moderação Híbrida**: O salvamento de novos comentários de alunos em questões passa pela camada local de moderação (`verificar_texto_improprio`) impedindo termos chulos ou ataques na comunidade de estudantes.

---
> [!NOTE]
> **Tabelas de Cache Operacionais**:
> *   `explicacoes_ia`: Armazena explicações brutas associadas a cada ID de questão.
> *   `ia_cache_estudo`: Centraliza em JSON os resumos e flashcards categorizados gerados por IA, eliminando requisições repetidas de OpenAI para a mesma questão acadêmica no ecossistema global.
