# Documentação Técnica: `app.py`

## Descrição Geral
O `app.py` é o núcleo operacional da plataforma. Ele é responsável por orquestrar a inicialização do Flask, integrar a camada de dados (Supabase), segurança (Talisman/Limiter) e gerenciar a modularização via Blueprints.

---

## Ciclo de Vida e Inicialização

### 1. Configurações de Ambiente e Segurança
- **Sessão**: Utiliza cookies de sessão (`HttpOnly`, `SameSite=Lax`) **sem** a flag `Secure`, compatíveis com execução local via HTTP puro — a aplicação é local/desktop e não exige HTTPS nem certificado TLS.
  > [!NOTE]
  > O `force_https`, o `session_cookie_secure` e o `strict_transport_security` (header HSTS) do Talisman estão desativados no código (`False`) — nos dois apps (`app.py` e `app_admin.py`). Isso é essencial: com `session_cookie_secure=True` (default da biblioteca), o Talisman sobrescreve a configuração do Flask a cada requisição e marca o cookie como `Secure`, fazendo os navegadores descartarem a sessão em ambiente HTTP sem TLS; o `strict_transport_security=False` elimina o último resquício da era web, pois o header `Strict-Transport-Security` não faz sentido em execução local.
- **Proteção de Cabeçalhos (Talisman)**: O **Talisman** é utilizado para implementar uma política de **Content Security Policy (CSP)** extremamente rigorosa, listando as origens válidas para scripts, fontes, mídias e conexões, mitigando de forma agressiva ataques de Injeção de Código (XSS) e Clickjacking.
- **Rate Limiting (Limiter)**: Integrado globalmente para evitar abusos na API e ataques de força bruta. Ele interage com o IP real dos clientes através do `ProxyFix`.
- **ProxyFix**: Configurado de forma flexível de acordo com a variável `TRUSTED_PROXIES` no `.env`. Em execução local/desktop, permite interpretar corretamente o IP e o protocolo (HTTP) do cliente; caso a aplicação venha a operar atrás de um proxy reverso, o mesmo mecanismo continua válido.

### 2. Compactação Gzip Nativa
O sistema implementa compactação Gzip automática em tempo real para otimização de banda de rede:
- A compactação é gerenciada pelo `@app.after_request` em conjunto com `Compress(app)`.
- Aplica-se exclusivamente a respostas com status HTTP de sucesso (entre `200` e `299`).
- Filtra por tipos MIME de texto e dados estruturados: `text/html`, `text/css`, `application/javascript` e `application/json`.
- Respostas já marcadas com `Content-Encoding` ou cujo navegador de destino não sinalize aceitação de gzip no cabeçalho `Accept-Encoding` são desconsideradas.

### 3. Ambiente Administrativo Separado (`app_admin.py`)
O painel administrativo **não faz parte** desta aplicação. Desde o split de ambientes, todo o backoffice (login com senha + 2FA/TOTP, gestão de questões e taxonomia, feedbacks) vive em um **repositório privado separado** (`gabaritei-admin`, aplicação `app_admin.py`) — este repositório público contém apenas o app do aluno:
- O `app.py` é **exclusivo do aluno** — sem nenhuma rota, código, template ou asset administrativo. É este app que será empacotado no Electron.
- O `app_admin.py` roda standalone (`python app_admin.py`, porta `ADMIN_PORT`, padrão 5001) com templates (`admin_templates/`) e assets (`admin_static/`) próprios, registrando os blueprints `admin` (sob o prefixo padrão `/admin`) e `admin_api` (sem prefixo, preservando os paths `/api/*` chamados pelo JS do painel).
- A raiz `/` redireciona direto para o login do painel (`/admin/login`) — modelo desktop local: sem honeypot nem prefixo obscuro (remanescentes da era web, removidos).
- **Auditoria (`logs_admin`)**: toda alteração feita por administradores no painel (INSERT/UPDATE/DELETE em `questoes`, `alternativas_questao`, `provas_origem`, `textos_base`, `materias`, `topicos`, `subtopicos`, `orgaos`, `cargos`, `feedbacks_questoes`) é registrada na tabela `logs_admin` com **quem** (`id_admin` + `username_admin` denormalizado), **qual tabela**, **tipo de alteração**, registro afetado, detalhes e **quando** (data + hora com timezone). Inserções via script (Extrator, rota de bulk) são logadas como `extrator-script`. Consulta em `/admin/logs` com filtros de tabela, ação, admin, registro e período, com paginação.
- **Credenciais isoladas (`admins`)**: administradores vivem na tabela própria `admins` (username, `password_hash`, `totp_secret`, `session_token` — migration `split_usuarios_admins`, IDs preservados). A tabela `usuarios` é exclusiva dos alunos (username + email opcional + `meta_diaria` + `tema`) — os dois apps não compartilham mais nenhuma tabela de credenciais.
- **Chaves e RLS (`rls_policies_aluno`)**: o app do aluno usa a `SUPABASE_ANON_KEY` via `banco_dados_aluno.py` (pública, protegida por RLS — conteúdo SELECT; cache IA/stats e feedbacks SELECT+INSERT; dados do aluno FOR ALL; `admins`/`logs_admin` deny-all; storage de imagens SELECT). A `service_role` (`SUPABASE_KEY` em `banco_dados.py`) é exclusiva do painel e **jamais embarca no bundle Electron**.
- **Hardening P1 (`security_hardening_p1`)**: questões pendentes invisíveis ao anon (só `status='publicada'` em `questoes`/`alternativas_questao`); upload de storage exclusivo do painel (service_role, 5MB, só imagens); `REVOKE` de `TRUNCATE` de anon em todas as tabelas, de escrita nas tabelas de conteúdo e de tudo em `admins`/`logs_admin`. Ambos os apps escutam apenas `127.0.0.1` (modelo desktop local).

### 4. Modularização por Blueprints (11 Módulos)
A aplicação do aluno é decomposta em 11 Blueprints independentes organizados sob a pasta `rotas/`:
1.  **`auth`**: Login real com e-mail + senha via Supabase Auth — cadastro (`/aluno/criar`), entrada (`/aluno/entrar`), recuperação de senha (`/aluno/esqueci`) e logout; a sessão é lembrada entre execuções pelo refresh token guardado na sessão Flask.
2.  **`aluno`**: Painel principal do estudante (Dashboard) e área de estudos geral.
3.  **`api`**: Endpoints internos para requisições assíncronas feitas pelo frontend.
4.  **`simulado`**: Criação, resposta e cálculo de pontuações de simulados inteiros.
5.  **`edital`**: Exibição e análise estruturada de editais de concursos abertos e previstos.
6.  **`conta`**: Gerenciamento de perfil e preferências do usuário logado (atualização, reset de dados de estudo e exclusão da conta).
7.  **`caderno`**: Funcionalidades de cadernos de questões agrupadas sob medida pelo estudante.
8.  **`filtro`**: Controle e aplicação de filtros complexos de disciplinas, bancas e anos.
9.  **`questao`**: Fluxo de exibição, resposta, gabaritos comentados e discussões de questões isoladas.
10. **`flashcards`**: Sistema de memorização espaçada (SRS), listagem de revisões do dia e status de cartões.
11. **`resumos`**: Caderno de resumos por matéria, com geração automática via IA e exclusão individual ou do caderno inteiro.

> [!NOTE]
> Os módulos administrativos (`admin`, `admin_api`) vivem no repositório privado `gabaritei-admin` e não existem neste repositório.

### 5. Gestão de Sessão Crítica (`load_user`)
A função principal do `login_manager` executa validação a cada requisição:
- **Resiliência e Retentativa**: Possui um fluxo integrado de tratamento de erros com até 3 tentativas sequenciais com pequenos delays caso ocorra uma instabilidade momentânea na conexão do Supabase.
- **Modelo Auth por usuário**: alunos autenticam com e-mail + senha (Supabase Auth); o `load_user` reconstrói o objeto `User` a partir do registro do banco e o `before_request` do app reaplica o JWT do aluno logado quando o processo reinicia (refresh token persistido na sessão Flask). A trava `session_token` permanece exclusiva do painel administrativo.

### 6. Interface Dinâmica e Injeção de Contexto (`context_processor`)
Para evitar que rotas repitam chamadas redundantes a serviços globais, a função `inject_global_data` disponibiliza automaticamente para todos os arquivos HTML as seguintes propriedades dinâmicas:
- **`is_premium`**: Booleano fixo `True` (no modelo software livre, todo usuário autenticado).
- **`global_streak`**: Ofensiva (dias consecutivos de estudo) calculada via `calcular_ofensiva_usuario`.
- **`global_flashcards_revisar`**: Total de flashcards agendados para revisão do dia.

---

## Logging Estruturado
Configurado no nível `INFO` com padrão estrito:
`[Data Hora] [Nível de Gravidade] Nome_do_Modulo: Mensagem`
Essencial para registrar anomalias de autenticação de sessão múltipla, problemas de conectividade e o status operacional da aplicação.
