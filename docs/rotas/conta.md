# Documentação Técnica: `rotas/conta.py` (Módulo de Gestão de Conta e Perfil)

## Descrição Geral
O módulo de gestão de conta (`rotas/conta.py`) é responsável por orquestrar todas as operações relacionadas ao perfil pessoal do aluno na plataforma **Gabaritei Questões**. Ele rege as atualizações de dados cadastrais (nome de usuário e e-mail) e disponibiliza recursos para o reset completo de dados acadêmicos ou exclusão permanente do perfil e dos dados do app. As operações destrutivas são protegidas por travas de confirmação textual e integradas de forma resiliente às regras de banco de dados para atender aos requisitos de privacidade de dados (LGPD).

---

## Funcionalidades e Fluxos Técnicos

### 1. Atualização Cadastral (`/aluno/conta/`)
Permite ao aluno alterar seu nome de usuário e e-mail de contato. O login é feito com e-mail + senha no Supabase Auth; esta tela não pede a senha para atualizar o perfil.
*   **Métodos HTTP**: `GET` e `POST` (configurada com `strict_slashes=False` para flexibilidade de roteamento).
*   **Segurança**: Acesso restrito a alunos autenticados através do decorator `@aluno_required`.
*   **Fluxo simplificado**: o formulário submete `username` e `email` diretamente — sem senha de confirmação (a identidade já é garantida pelo login do Auth com e-mail + senha).
*   **Persistência**: Grava as alterações na tabela `usuarios` baseando-se no ID do aluno logado.

> [!NOTE]
> A rota atualiza apenas `usuarios.username` e `usuarios.email`. Ela **não** altera o e-mail da conta no Supabase Auth (`auth.users`), que continua sendo o credencial de login; para trocar o e-mail de acesso seria necessário um fluxo próprio no Auth.

---

### 2. Purgação Total de Dados de Estudos (`/aluno/conta/resetar-dados`)
Recurso avançado que permite ao aluno limpar de forma irrecuperável todo o seu histórico acadêmico e reiniciar seus estudos do zero, sem excluir a conta principal.
*   **Método HTTP**: `POST`
*   **Trava de Segurança**:
    *   *Confirmação Textual*: Exige que o usuário digite no formulário a frase obrigatória exata **`"RESETAR MEUS DADOS"`**. O sistema aplica limpeza de espaços em branco e formatação em caixa alta (`texto_confirmacao.strip().upper()`) antes da comparação.
*   **A Execução Sequencial de Deleção (13 operações no Supabase)**:
    Caso a trava textual seja validada, o sistema dispara a limpeza no banco de dados na seguinte ordem:
    1.  **Reinicialização da Meta**: Atualiza `usuarios.meta_diaria = 0` do aluno.
    2.  **Exclusão de Respostas**: Deleta `historico_respostas` filtrando por `id_usuario`.
    3.  **Exclusão de Cadernos**: Deleta `cadernos`; o `ON DELETE CASCADE` limpa `caderno_questoes`.
    4.  **Exclusão de Filtros Salvos**: Deleta `filtros_salvos`.
    5.  **Exclusão de Categorias de Flashcards**: Deleta `flashcard_categorias`.
    6.  **Exclusão de Flashcards**: Deleta `flashcards`.
    7.  **Exclusão de Simulados**: Deleta `simulados` com `id_criador == user_id`; resultados e questões vinculadas caem em cascata.
    8.  **Exclusão de Ciclos de Editais**: Deleta `editais_ciclo`.
    9.  **Exclusão de Matérias do Edital**: Deleta `editais_materias` (tabelas com dono desde `auth_usuario_e_policies`).
    10. **Exclusão de Tópicos do Edital**: Deleta `editais_topicos`.
    11. **Exclusão de Progresso de Editais**: Deleta `editais_progresso`.
    12. **Exclusão de Comentários**: Deleta `comentarios_questao` do aluno.
    13. **Exclusão de Denúncias**: Deleta `reports_comentarios` do aluno (ver [docs/banco_dados.md](../banco_dados.md)).

    Todas as operações passam por `safe_execute`; uma exceção interrompe o bloco e exibe um flash de erro, sem concluir o reset.

---

### 3. Exclusão Permanente de Conta (`/aluno/conta/excluir`)
Implementa o fluxo irreversível de exclusão do perfil do aluno e dos dados do app, garantindo o direito ao esquecimento no escopo deste repositório (a conta em `auth.users` é tratada à parte — ver nota abaixo).
*   **Método HTTP**: `POST`
*   **Trava de Segurança**:
    *   *Confirmação Textual*: Exige que o usuário digite de forma deliberada a frase mestre **`"EXCLUIR MINHA CONTA"`**.
*   **O Fluxo de Purgação e Medidas Anti-Fraude**:
    1.  **Exclusão de Denúncias**: Remove `reports_comentarios` do aluno (LGPD).
    2.  **Exclusão do Registro Principal**: Remove a linha do aluno em `usuarios`; o banco aplica as cascatas nas tabelas de dados de estudo.
    3.  **Exclusão da Chave de IA Local**: Chama `remover_config_ia(current_user.id)` para apagar a configuração BYOK deste dispositivo. Uma falha aqui é registrada em log, mas não impede o restante do fluxo.
    4.  **Destruição de Sessões e Cookies**: Invoca `logout_user()` do Flask-Login para limpar a sessão e o cookie local. O sistema emite uma mensagem informativa e redireciona o navegador para a Home Page (`/`).

> [!NOTE]
> A conta em `auth.users` **não** é removida por esta rota: o app do aluno usa apenas a ANON key e o JWT do usuário, sem `service_role` para administrar usuários do Supabase Auth. A rota remove o perfil, as denúncias e a chave local (falhas ao apagar a chave são apenas logadas) e encerra a sessão; a remoção da conta Auth é uma operação administrativa no painel/repositório separado.

### 4. Configuração de IA — BYOK (`/api/ia/config`)
O aluno usa a **própria chave de API** (OpenAI, Google Gemini ou Anthropic) para os recursos de IA (ver [docs/ia.md](../ia.md)).
*   **Método HTTP**: `POST` (JSON: `provedor`, `modelo`, `chave`).
*   **Segurança**: `@aluno_required` + CSRF global (`X-CSRFToken`).
*   **Validações**: provedor precisa estar nas listas oficiais de `provedores_ia.PROVEDORES`; chave com mínimo de 20 caracteres; modelo em branco assume o padrão do provedor (modelo personalizado é aceito até 80 caracteres).
*   **Ping gratuito**: `testar_chave()` valida chave E modelo com 2 GETs em `/models` (sem gastar tokens). Falha → `400` com o motivo (ex.: "Chave de API inválida.").
*   **Persistência local**: grava via `banco_local.salvar_config_ia()` — SQLite + **DPAPI** em `GABARITEI_LOCAL_DIR` (userData do Electron). **Nada vai ao Supabase**.
*   **Resposta**: `{"success": true, "status": {...}}` — o `status` contém apenas a **máscara** da chave (`sk-1…5555`); a chave completa jamais retorna ao front ou vai a logs.

### 5. Remoção da Chave de IA (`/api/ia/config/remover`)
Apaga a configuração local do dispositivo (direito ao esquecimento/LGPD).
*   **Método HTTP**: `POST` (sem corpo; CSRF via header).
*   **Comportamento**: `banco_local.remover_config_ia(current_user.id)`.
*   **Resposta**: `{"success": true, "removido": <bool>}` — `removido` indica se havia configuração para apagar; chamadas repetidas continuam retornando `success: true` (idempotente).

---

## Detalhes de Segurança e Diretrizes de Privacidade

> [!CAUTION]
> A exclusão de conta remove o perfil em `usuarios` e os dados vinculados por cascata, mas **não é uma transação única**: são chamadas separadas via PostgREST. Uma falha no meio do processo pode deixar parte dos dados já removida, e a conta em `auth.users` permanece. Trate a remoção da conta Auth como operação administrativa no painel/repositório separado.

*   **Integridade Operacional**: Cada escrita ou deleção no Supabase é encapsulada no wrapper `safe_execute()`, que repete a chamada e registra erros com `logger.error`; ele **não** agrupa as 13 operações do reset em uma transação única, então o reset também não é atômico entre etapas.
