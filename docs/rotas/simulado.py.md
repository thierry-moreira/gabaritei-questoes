# Documentação Técnica: `rotas/simulado.py` (Provas Simuladas)

## Descrição Geral
O módulo de Simulados implementa o ecossistema de exames cronometrados personalizados do Gabaritei Questões. Disponível para todo aluno autenticado (modelo software livre), ele permite criar e realizar simulados públicos ou privados gerados dinamicamente com base em múltiplos filtros taxonômicos e organizacionais, participar de classificações em tempo real e exportar cadernos de prova profissionais no formato PDF.

---

## Ciclo de Vida do Simulado (Geração Dinâmica e Rollback)

O fluxo de processamento de um simulado compreende a criação do cabeçalho físico, a varredura dinâmica e o sorteio de questões no banco e, caso os critérios sejam restritivos a ponto de não retornarem questões suficientes, a limpeza física dos registros órfãos:

```mermaid
sequenceDiagram
    autonumber
    actor Aluno
    participant S as Simulado (rotas/simulado.py)
    participant DB as Supabase (Banco de Dados)

    Aluno->>S: Definir título, privacidade e filtros avançados
    S->>DB: Inserir cabeçalho em 'simulados'
    DB-->>S: Retornar 'id_simulado'
    
    rect rgb(25, 25, 35)
        note over S: Varredura de Filtros por Matéria e Tópicos
        S->>DB: Consultar view_questoes_completa (limit 500)
        DB-->>S: Retornar pool de questões candidatas
        
        alt Pool de Questões >= Quantidade Solicitada
            note over S: Executa sorteio random.sample(pool, qtd)
            S->>DB: Salvar em 'simulados_questoes' (lote associativo)
            S-->>Aluno: Confirmar geração com sucesso!
        else Pool de Questões < Quantidade Solicitada e > 0
            note over S: Sorteia todas as candidatas do Pool
            S->>DB: Salvar em 'simulados_questoes' (lote associativo)
            S-->>Aluno: Confirmar geração com sucesso parcial!
        else Pool de Questões = 0 (Vazio)
            note over S: Mecanismo de Auto-Rollback Transacional
            S->>DB: Deletar cabeçalho em 'simulados' (id_simulado)
            S-->>Aluno: Exibir alerta: Questões insuficientes.
        end
    end
```

---

## Motor de Sorteio e Filtros Avançados

O sorteio baseia-se na visão SQL materializada `view_questoes_completa`, que consolida em uma única tabela todos os metadados de escolaridade, bancas, órgãos, cargos, tópicos e anos.
O algoritmo Python executa as requisições em lote para cada par de Matéria/Tópico parametrizado, coletando um subconjunto de até 500 candidatos e reduzindo a massa por meio da função estocástica de alta performance do Python:

```python
if len(pool_questoes) > qtd:
    sorteadas = random.sample(pool_questoes, qtd)
else:
    sorteadas = pool_questoes
```

---

## Detalhamento das Rotas e APIs

### 0. Guard único de acesso (`_simulado_do_usuario_ou_none`)

Toda rota que recebe `id_simulado` (fazer, corrigir, ranking e PDF) chama o
mesmo guard antes de qualquer consulta de questões, gabarito, resultados ou
RPC:

```python
def _simulado_do_usuario_ou_none(id_simulado):
    simulado = _buscar_simulado(id_simulado)
    if not simulado:
        return None
    if simulado.get('eh_privado') and simulado.get('id_criador') != current_user.id:
        return None
    return simulado
```

`_buscar_simulado` consulta primeiro a tabela `simulados` (RLS owner-only) e
depois `view_simulados_publicos` (somente `eh_privado=false`, sem
`id_criador`/e-mail). O guard acrescenta a checagem explícita de
`eh_privado`/`id_criador`, mantendo o contrato mesmo se a origem da consulta
mudar.

| Situação | Resultado |
|---|---|
| Simulado inexistente | `None` → flash "Simulado não encontrado." + redirect |
| Simulado privado de outro aluno | `None` → mesma resposta do inexistente |
| Simulado público de qualquer aluno | Permitido |
| Simulado do próprio aluno (público ou privado) | Permitido |

Como o guard roda antes de `_ids_questoes_do_simulado`, o não-dono não chega
a carregar questões, não consulta `alternativas_questao.is_correct` (gabarito),
não insere em `simulados_resultados` e não chama `ranking_simulado`.

### 1. Painel de Controle (`/aluno/simulados`)
*   **Método**: `GET`
*   **Segurança**: `@aluno_required`
*   **Isenção de Rate Limits**: `@limiter.exempt`
*   **Descrição**: Exibe a interface central de provas. Realiza duas varreduras paralelas no banco de dados Supabase:
    1.  **Simulados Públicos**: Aberto para todos os alunos autenticados, carregando o autor através de junção com a tabela de usuários (`usuarios(username)`).
    2.  **Simulados Privados**: Filtrados estritamente pelo ID do estudante logado.
    Também carrega listas taxonômicas (bancas, órgãos, matérias e cargos) para municiar o modal dinâmico de filtros.

### 2. Geração Dinâmica (`/aluno/simulados/gerar`)
*   **Método**: `POST`
*   **Segurança**: `@aluno_required`
*   **Isenção de Rate Limits**: `@limiter.exempt`
*   **Lógica**: Processa formulários com múltiplos vetores de restrição. Em caso de falhas sistêmicas ou problemas de rede com o banco durante as inserções em lote, captura a exceção em um bloco `try/except` que dispara uma rotina física de rollback apagando imediatamente a "capa" criada na tabela `simulados` para impedir registros órfãos ou inconsistentes na plataforma.

### 3. Interface de Execução (`/aluno/simulados/fazer/<id_simulado>`)
*   **Método**: `GET`
*   **Segurança**: `@aluno_required`
*   **Isenção de Rate Limits**: `@limiter.exempt`
*   **Blindagem de Privacidade**:
    Chama `_simulado_do_usuario_ou_none(id_simulado)` antes de carregar a prova. Simulado privado de outro aluno e simulado inexistente recebem a mesma resposta (flash + redirect), sem revelar a existência do ID. Simulado público de qualquer aluno e simulado do próprio aluno (inclusive privado) seguem normalmente.
*   **Uniformidade Psicológica (Anti-Memorização)**:
    Para assegurar a eficácia dos testes, as questões recuperadas do banco são baralhadas aleatoriamente em memória antes de serem entregues ao frontend através da função:
    ```python
    random.shuffle(questoes)
    ```
    Isso impede que o aluno aprenda a ordem sequencial das questões ou decore as respostas baseando-se no posicionamento visual das folhas de prova. As alternativas dentro de cada questão permanecem organizadas lexicograficamente pela letra (`A`, `B`, `C`...) para coerência textual do exame.

### 4. Correção Automática (`/aluno/simulados/corrigir/<id_simulado>`)
*   **Método**: `POST`
*   **Segurança**: `_simulado_do_usuario_ou_none(id_simulado)` antes de qualquer consulta. Simulado privado de outro aluno não chega a carregar gabarito, não insere resultado e não chama a RPC de ranking.
*   **Lógica**:
    *   Busca as alternativas marcadas como corretas (`is_correct = True`) para os IDs das questões que integram o simulado.
    *   Compara item a item com as submissões via formulário do aluno (`resp_{q_id}`).
    *   Calcula a nota em escala de `0` a `10` e grava na tabela `simulados_resultados`.
    *   Busca em tempo real o **Top 10 Global** de notas via RPC `ranking_simulado` (público para qualquer autenticado; privado apenas para o criador).

### 5. API de Exclusão (`/aluno/simulados/excluir/<id_simulado>`)
*   **Método**: `POST`
*   **Proteção Contra IDOR**:
    Garante que apenas o criador original possa realizar a deleção. Valida a ownership antes da transação física no banco:
    ```python
    res = safe_execute(
        supabase.table('simulados').select('id_criador').eq('id', id_simulado).limit(1)
    )
    if res.data and res.data[0].get('id_criador') == current_user.id:
        safe_execute(supabase.table('simulados').delete().eq('id', id_simulado))
    ```
    `.limit(1)` em vez de `.single()` evita o erro PGRST116 de "0 linhas" e
    mantém a resposta igual para "não existe" e "não é seu".

### 6. Ranking (`/aluno/simulados/ranking/<id_simulado>`)
*   **Método**: `GET`
*   **Segurança (F-05)**: chama `_simulado_do_usuario_ou_none(id_simulado)` antes da RPC. Simulado privado de outro aluno e simulado inexistente recebem a mesma resposta (flash + redirect), sem consultar ranking/resultados; o guard também compara `id_criador` caso a tabela devolva indevidamente a linha. A RPC `ranking_simulado` repete a validação no banco (público: authenticated; privado: criador) e devolve somente username + métricas. Regressão: `test_ranking_privado_alheio_bloqueia_mesmo_se_consulta_devolver_linha`.

---

## Exportação PDF — Prévia Navegável Unificada (padrão dos resumos)

A rota `/simulado/<id_simulado>/pdf` entrega **sempre** a prévia navegável da prova (`simulados/pdf_preview.html`) com o botão **"Imprimir / Salvar PDF"** — a mesma experiência implementada nos resumos. O fluxo é client-side, sem renderização de PDF no servidor. Antes de montar a prévia, a rota chama `_simulado_do_usuario_ou_none(id_simulado)`: simulado privado de outro aluno e simulado inexistente recebem a mesma resposta (flash + redirect) e nenhuma questão/alternativa/gabarito é consultada.

```mermaid
graph TD
    A[Chamada de PDF] --> B[Recuperar Questões & Alternativas]
    B --> C[Aplicar Fallback de Gabarito]
    C --> D[Renderizar Jinja2: simulados/pdf_preview.html]
    D --> E{imprimirOuPDF - imprimir_ou_pdf.js}
    E -->|Desktop Electron| F[electronAPI.printToPDF → PDF nativo]
    E -->|Navegador| G[window.print → Salvar como PDF]
```

*   **Desktop (Electron)**: o Chromium do Electron não renderiza `application/pdf` inline; `imprimir_ou_pdf.js` detecta o `electronAPI` e gera o PDF nativo (A4), aberto no leitor padrão do sistema.
*   **Navegador**: `window.print()` abre o preview de impressão nativo — o `@media print` da página esconde a barra de ações e expande a folha A4; o aluno usa **"Salvar como PDF"**.
*   O corpo da prova (`_pdf_corpo.html`) e a folha de estilos (`pdf_style.css`) são compartilhados: a folha renderizada na tela é a mesma que sai na impressão. (O antigo pipeline WeasyPrint — template `pdf.html` e URIs `file:///` — foi removido do fluxo; o `build.ps1` ainda baixa um runtime GTK legado, mas o backend não o usa.)

### Algoritmo Específico de Fallback do Gabarito
Para garantir que o caderno impresso traga as respostas corretas de cada questão de forma impecável no final do documento (gabarito automático), foi projetada uma varredura hierárquica em dois níveis:
```python
# 1º Nível: Procura metadados gravados na própria estrutura simplificada da questão
letra_certa = q.get('gabarito') or q.get('alternativa_correta') or q.get('resposta') or q.get('resposta_correta')

# 2º Nível: Se nulo, varre as alternativas associadas em busca de sinalizadores booleanos do Supabase
if not letra_certa:
    for a in q['alternativas_questao']:
        if a.get('is_correta') or a.get('correta') or a.get('certa') or a.get('gabarito'):
            letra_certa = a.get('letra')
            break

q['letra_gabarito'] = letra_certa if letra_certa else 'N/A'
```

---

## Segurança de Transações de Banco de Dados

| Operação | Mecanismo de Integridade | Comportamento Técnico |
| :--- | :--- | :--- |
| **Exclusão de Simulado** | `ON DELETE CASCADE` | Ao deletar o cabeçalho físico, as chaves estrangeiras apagam automaticamente todos os registros associativos nas tabelas `simulados_questoes` e `simulados_resultados` em nível de banco de dados (Supabase/PostgreSQL) de forma atômica. |
| **Acesso Autenticado** | Decorator de Nível de Blueprint | Exige autenticação de aluno (`@aluno_required`) em todas as rotas de simulado — no modelo software livre, todo aluno autenticado tem acesso completo. |
| **Blindagem de Ownership** | Guard único + RLS | `_simulado_do_usuario_ou_none` é chamado por fazer/corrigir/ranking/PDF antes de qualquer consulta; simulado privado alheio e inexistente têm a mesma resposta. No banco, `simulados_resultados` exige simulado público ou do próprio aluno no INSERT/UPDATE (migration `simulados_resultados_visibilidade`). |

> [!WARNING]
> Falhas no carregamento da prévia (rede/Supabase) são capturadas no bloco `try/except` da rota, exibindo mensagens flash amigáveis na tela e registrando no terminal com a marcação `❌ Erro ao carregar o PDF do simulado: {e}`.
