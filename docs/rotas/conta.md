# Documentação Técnica: `rotas/conta.py` (Módulo de Gestão de Conta e Perfil)

## Descrição Geral
O módulo de gestão de conta (`rotas/conta.py`) é responsável por orquestrar todas as operações relacionadas ao perfil pessoal do aluno na plataforma **Gabaritei Questões**. Ele rege as atualizações de dados cadastrais (nome de usuário e e-mail) e disponibiliza recursos para o reset completo de dados acadêmicos ou exclusão permanente do cadastro. As operações destrutivas são protegidas por travas de confirmação textual e integradas de forma resiliente às regras de banco de dados para garantir conformidade estrita com regulamentações de privacidade de dados (LGPD).

---

## Funcionalidades e Fluxos Técnicos

### 1. Atualização Cadastral (`/aluno/conta/`)
Permite ao aluno alterar seu nome de usuário e e-mail de contato (no modelo desktop o aluno não possui senha).
*   **Métodos HTTP**: `GET` e `POST` (configurada com `strict_slashes=False` para flexibilidade de roteamento).
*   **Segurança**: Acesso restrito a alunos autenticados através do decorator `@aluno_required`.
*   **Fluxo simplificado**: o formulário submete `username` e `email` diretamente — sem senha de confirmação (a identidade já é garantida pelo login do Auth com e-mail + senha).
*   **Persistência**: Grava as alterações na tabela `usuarios` baseando-se no ID do aluno logado.

---

### 2. Purgação Total de Dados de Estudos (`/aluno/conta/resetar-dados`)
Recurso avançado que permite ao aluno limpar de forma irrecuperável todo o seu histórico acadêmico e reiniciar seus estudos do zero, sem excluir a conta principal.
*   **Método HTTP**: `POST`
*   **Trava de Segurança**:
    *   *Confirmação Textual*: Exige que o usuário digite no formulário a frase obrigatória exata **`"RESETAR MEUS DADOS"`**. O sistema aplica limpeza de espaços em branco e formatação em caixa alta (`texto_confirmacao.strip().upper()`) antes da comparação.
*   **A Execução Sequencial de Deleção (13 operações no Supabase)**:
    Caso a trava textual seja validada, o sistema dispara a limpeza em lotes no banco de dados seguindo a ordem lógica:
    1.  **Reinicialização da Meta**: Atualiza o registro do usuário na tabela `usuarios` zerando a meta diária de estudos:
        `meta_diaria = 0`.
    2.  **Exclusão de Respostas**: Deleta todos os registros de resoluções de questões associados na tabela `historico_respostas` filtrando por `id_usuario`.
    3.  **Exclusão de Cadernos**: Deleta as coleções pessoais de questões em `cadernos`. A configuração interna de chave estrangeira no Supabase com gatilho `ON DELETE CASCADE` limpa automaticamente as amarrações em `caderno_questoes`.
    4.  **Exclusão de Filtros Salvos**: Deleta as configurações de filtros acadêmicos na tabela `filtros_salvos`.
    5.  **Exclusão de Flashcards**: Remove os baralhos personalizados e cartões individuais nas tabelas `flashcard_categorias` e `flashcards`.
    6.  **Exclusão de Simulados**: Deleta os simulados em `simulados` criados pelo aluno (`id_criador == user_id`). A exclusão dispara em cascata a purgação de tabelas de resultados e questões vinculadas.
    7.  **Exclusão de Ciclos de Editais**: Deleta os registros na tabela `editais_ciclo`.
    8.  **Exclusão do Progresso de Editais**: Remove `editais_materias`, `editais_topicos` e `editais_progresso` (tabelas com dono desde `auth_usuario_e_policies`).
    9.  **Exclusão de Comentários**: Remove contribuições postadas pelo usuário na tabela `comentarios_questao`.
    10. **Exclusão de Denúncias**: Remove as denúncias feitas pelo aluno na tabela `reports_comentarios` (com dono — ver [docs/banco_dados.md](../banco_dados.md)).

---

### 3. Exclusão Permanente de Conta (`/aluno/conta/excluir`)
Implementa o fluxo irreversível de destruição de contas, garantindo o direito ao esquecimento e a conformidade da plataforma com a LGPD.
*   **Método HTTP**: `POST`
*   **Trava de Segurança**:
    *   *Confirmação Textual*: Exige que o usuário digite de forma deliberada a frase mestre **`"EXCLUIR MINHA CONTA"`**.
*   **O Fluxo de Purgação e Medidas Anti-Fraude**:
    1.  **Exclusão do Registro Principal**
    3.  **Destruição de Sessões e Cookies**: Invoca imediatamente o método `logout_user()` do Flask-Login para limpar as credenciais salvas em memória RAM no servidor e anular os tokens de cookies locais no navegador do usuário. O sistema emite uma mensagem informativa de encerramento amigável e redireciona o navegador do usuário de volta para a Home Page (`/`).

### 4. Configuração de IA — BYOK (`/api/ia/config`)
O aluno usa a **própria chave de API** (OpenAI, Google Gemini ou Anthropic) para os recursos de IA (ver [docs/ia.md](../ia.md)).
*   **Método HTTP**: `POST` (JSON: `provedor`, `modelo`, `chave`).
*   **Segurança**: `@aluno_required` + CSRF global (`X-CSRFToken`).
*   **Validações**: provedor precisa estar nas listas oficiais de `provedores_ia.PROVEDORES`; chave com mínimo de 20 caracteres; modelo em branco assume o padrão do provedor (também aceita modelo personalizado).
*   **Ping gratuito**: `testar_chave()` valida chave E modelo com 2 GETs em `/models` (sem gastar tokens). Falha → `400` com o motivo (ex.: "Chave de API inválida.").
*   **Persistência local**: grava via `banco_local.salvar_config_ia()` — SQLite + **DPAPI** em `GABARITEI_LOCAL_DIR` (userData do Electron). **Nada vai ao Supabase**.
*   **Resposta**: `{"success": true, "status": {...}}` — o `status` contém apenas a **máscara** da chave (`sk-1…5555`); a chave completa jamais retorna ao front ou vai a logs.

### 5. Remoção da Chave de IA (`/api/ia/config/remover`)
Apaga a configuração local do dispositivo (direito ao esquecimento/LGPD).
*   **Método HTTP**: `POST` (sem corpo; CSRF via header).
*   **Comportamento**: `banco_local.remover_config_ia(current_user.id)` — sempre responde `{"success": true}` (idempotente).

---

## Detalhes de Segurança e Diretrizes de Privacidade

> [!CAUTION]
> A deleção permanente de contas no Supabase é uma transação atômica e irreversível devido às restrições de chaves estrangeiras com cascata no banco de dados.

*   **Integridade Operacional**: Todas as operações que efetuam escritas de atualização ou deleções no banco de dados Supabase são encapsuladas no wrapper seguro `safe_execute()`. Caso ocorram falhas momentâneas de latência ou perda de rede, o banco de dados desfaz as transações não completadas de forma a evitar estados corrompidos, e o Flask registra um log detalhado do erro (`logger.error`) enquanto exibe um erro amigável ao aluno.
