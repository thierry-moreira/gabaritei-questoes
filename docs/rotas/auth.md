# Blueprint `auth` — Entrada do Desktop (Usuário Local, sem Senha)

> [!IMPORTANT]
> **Migração Desktop (software livre).** O modelo de autenticação por e-mail + senha foi **extinto** para alunos.
> O Gabaritei Questões agora é uma aplicação desktop de usuário local: na primeira execução o usuário cria seu perfil
> (apenas nome de usuário, e-mail opcional) e entra direto. Nas execuções seguintes a entrada é automática.
> O painel administrativo **mantém** senha + 2FA (ver `docs/rotas/admin.md`).

## Rotas Ativas

### 1. Entrada Automática (`/aluno/login`, GET)
*   **Redirecionamento de autenticados**: alunos vão direto à área do aluno. Contas com papel ≠ `aluno` são deslogadas com um aviso — o painel administrativo roda em aplicativo dedicado (`app_admin.py`).
*   **Usuário local existente**: `_buscar_aluno_local()` consulta `usuarios` filtrando `role == 'aluno'` (limit 1); encontrado, executa `login_user` e redireciona à área do aluno — entrada transparente, sem senha.
*   **Sem usuário local**: renderiza a tela de criação (`templates/auth/login.html`).

### 2. Criação do Usuário Local (`/aluno/criar`, POST)
*   **Formulário**: `username` (obrigatório, com strip) + `email` (opcional).
*   **Proteção CSRF**: token renderizado no formulário da tela de entrada.
*   **Idempotente**: se já existir usuário local, simplesmente entra direto (sem duplicar cadastro).
*   **Insert no Supabase**: grava `username`, `email` (quando informado) e `role = 'aluno'`; `meta_diaria`, `tema` e demais campos assumem os defaults do banco. Após o insert, efetua o login automático e redireciona à área do aluno.

### 3. Encerramento de Sessão (`/logout`)
*   Executa `logout_user()` e remove da sessão Flask **apenas as chaves não administrativas** (preserva `admin_*`), garantindo que um administrador autenticado em painel paralelo não seja desconectado.
*   Redireciona para a página de apresentação (`aluno.index`).

## Rotas Removidas (referência histórica)
| Rota | Motivo da remoção |
|---|---|
| `POST /aluno/login` (e-mail + senha) | Aluno desktop não possui senha; entrada é automática (POST responde 405). |
| `/aluno/cadastro` | Substituído por `/aluno/criar` (usuário local, sem e-mail/senha obrigatórios). |
| `/esqueci-senha` · `/redefinir-senha/<token>` | Sem senha não há o que recuperar. |
| `/verificar-email/<id>` · `/reenviar-codigo/<id>` | Sem senha/cadastro por e-mail não há verificação de conta. |

> **Colunas de banco extintas** (migration `drop_auth_columns_desktop_no_password`): `email_verificado`, `codigo_verificacao`, `token_recuperacao`, `expiracao_token`. As colunas `password_hash`, `session_token` e `totp_secret` foram movidas para a tabela `admins` (migration `split_usuarios_admins`) — a tabela `usuarios` é agora exclusiva dos alunos.
