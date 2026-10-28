# 🔌 Módulo de APIs de Suporte e Utilitários (`rotas/api.py`)

O módulo `api.py` centraliza endpoints de serviço baseados no padrão REST. Ele serve como ponte de alta performance entre o banco de dados (Supabase) e os componentes dinâmicos do frontend, alimentando filtros dinâmicos de busca e persistindo as preferências estéticas dos alunos.

---

## 📌 Detalhamento dos Endpoints e Lógica de Negócio

### 1. Carregamento Otimizado em Cascata (`/api/get_assuntos_cascata`)
Este é o endpoint mais crítico do módulo, projetado especificamente para alimentar seletores de múltiplos níveis (filtros de questões e criadores de editais) sem degradar a performance do banco.

*   **Rota**: `/api/get_assuntos_cascata`
*   **Método**: `POST`
*   **Segurança**:
    *   Leitura pública: a taxonomia é conteúdo público e as tabelas `topicos` e `subtopicos` liberam `SELECT` para o papel `anon` via RLS. Não depende de uma sessão Flask válida.
    *   Isento de rate limiting (`@limiter.exempt`) por ser um fluxo operacional intensivo do painel do aluno.
*   **Estrutura do JSON Input**:
    ```json
    {
      "ids_materias": [1, 2, 5]
    }
    ```
*   **Arquitetura Otimizada (Evitando Consultas N+1)**:
    Tradicionalmente, carregar subtópicos para múltiplos tópicos de várias matérias geraria dezenas de consultas recursivas ao banco. Este endpoint mitiga isso realizando **apenas 2 requisições eficientes** em lote:
    
    ```mermaid
    graph TD
        A[POST /api/get_assuntos_cascata] --> B{Possui ids_materias?}
        B -- Não --> C[Retorna Vazio]
        B -- Sim --> D[Consulta 1: Buscar todos os Tópicos das Matérias selecionadas via .in_]
        D --> E[Extrai IDs de Tópicos encontrados]
        E --> F[Consulta 2: Buscar todos os Subtópicos em lote via .in_]
        F --> G[Agrupamento em Árvore na Memória]
        G --> H[Retorna JSON Hierárquico]
    ```

*   **Algoritmo de Agrupamento**:
    1.  **Consulta 1 (Tópicos)**: Busca os tópicos associados às matérias enviadas no array usando o operador `.in_("id_materia", ids_materias)` com tratamento seguro de consultas.
    2.  **Extração de Chaves**: Mapeia em memória todos os `id_topico` resultantes.
    3.  **Consulta 2 (Subtópicos)**: Executa uma única busca por subtópicos cujos pais estejam no conjunto extraído (`.in_("id_topico", ids_topicos_encontrados)`).
    4.  **Montagem da Árvore**: Agrupa os subtópicos dentro de seus respectivos nós de tópicos pais utilizando list comprehensions otimizadas, entregando um formato estruturado:
        ```json
        [
          {
            "id": 10,
            "nome": "Direitos Fundamentais",
            "subtopicos": [
              { "id": 101, "nome": "Direito à Vida" },
              { "id": 102, "nome": "Princípio da Igualdade" }
            ]
          }
        ]
        ```

---

### 2. Carregamento de Tópicos por Matéria
*   **Rota**: `/api/topicos/<int:id_materia>`
*   **Método**: `GET`
*   **Segurança**: Protegido por rate limiter de **60 requisições por minuto** para mitigar tentativas de raspagem automatizada (scraping) de taxonomia.
*   **Lógica**: Retorna um array plano contendo todos os tópicos pertencentes à matéria informada, ordenados pelo Supabase.

---

### 3. Carregamento de Subtópicos por Tópico
*   **Rota**: `/api/subtopicos/<int:id_topico>`
*   **Método**: `GET`
*   **Segurança**: Rate limit de **60 requisições por minuto**.
*   **Lógica**: Retorna a lista plana de subtópicos vinculados ao tópico pai.

---

### 4. Filtro Dinâmico de Cargos por Órgão
*   **Rota**: `/api/cargos/<int:id_orgao>`
*   **Método**: `GET`
*   **Segurança**: Rate limit de **60 requisições por minuto**.
*   **Lógica**: Utilizado para atualizar dinamicamente o seletor de Cargos do frontend quando o aluno seleciona um Órgão/Instituição específico. Retorna os campos `id_cargo` e `nome_cargo` ordenados alfabeticamente.

---

### 5. Persistência de Preferências Estéticas
*   **Rota**: `/api/usuario/preferencias`
*   **Método**: `POST`
*   **Segurança**: Exige usuário autenticado (`@aluno_required`).
*   **JSON Input**:
    ```json
    {
      "tema": "dark"
    }
    ```
*   **Validação Rígida de Domínio**:
    O valor do parâmetro `tema` é verificado contra uma lista branca de valores aceitos: `['light', 'dark']`. Caso o cliente envie dados diferentes, o servidor rejeita imediatamente retornando `400 Bad Request` com a mensagem `"Tema inválido"`.
*   **Persistência**: 
    Atualiza o campo `tema` na tabela `usuarios` do Supabase para o ID correspondente ao usuário ativo na sessão (`current_user.id`), mantendo a consistência do tema entre navegadores e dispositivos diferentes.

---

## 🛡️ Camada de Segurança e Defesa

1.  **Prevenção contra Raspagem Dinâmica (Anti-Scraping)**:
    A taxonomia de questões (matérias, tópicos, subtópicos e órgãos) representa valor intelectual essencial do Gabaritei. A aplicação de rate limits agressivos nas rotas de leitura impede que scripts de terceiros extraiam recursivamente a estrutura taxonomista.
2.  **Validação Severa e Tipagem no Endpoint**:
    A conversão explícita de tipos de parâmetros dinâmicos de rota no Flask (ex: `<int:id_materia>`) atua como uma barreira prévia contra injeções SQL e parâmetros maliciosos nos roteadores.
3.  **Tratamento de Exceções Silencioso**:
    Erros de comunicação com o Supabase ou falhas de rede interna são capturados em blocos `try/except`. O erro detalhado é impresso de forma segura em logs internos do servidor, enquanto o cliente recebe respostas tratadas (`500 Internal Server Error` ou arrays vazios em requisições de listagem), impedindo o vazamento de detalhes técnicos da infraestrutura da plataforma.
