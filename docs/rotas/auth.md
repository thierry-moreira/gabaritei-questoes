# Blueprint `auth` — Login com E-mail e Senha (Supabase Auth)

> [!IMPORTANT]
> **Autenticação real por usuário.** Cada aluno tem conta própria (e-mail + senha) no **Supabase Auth** — o progresso fica na nuvem e acompanha o usuário em qualquer máquina.
> O vínculo é feito por `usuarios.auth_id` (migration `auth_usuario_e_policies`); a escrita no banco exige, além do header `x-app-token`, que o `auth.uid()` do JWT bata com o dono da linha (RLS por dono).
> O painel administrativo mantém o próprio login (senha + 2FA, tabela `admins`; ver `docs/rotas/admin.md` no repo do painel).

## Rotas Ativas

### 1. Tela de Login / Sessão Lembrada (`/aluno/login`, GET)
*   **Redirecionamento de autenticados**: alunos logados vão direto à área do aluno.
*   **Sessão lembrada**: se houver um refresh token salvo na sessão Flask (`auth_refresh_token` — gravado no login), o client Supabase é reautenticado (`restaurar_sessao`) e o aluno entra sem redigitar a senha; o perfil é reconstituído via `usuarios.auth_id`. Refresh inválido/expirado → token descartado e tela normal.
*   **Client reautenticado a cada boot**: o `before_request` de `app.py` reaplica o JWT do aluno logado quando o processo Flask reinicia (o client global perde a sessão em memória; o refresh token vive no cookie de sessão Flask, persistido pela `FLASK_SECRET_KEY` fixa do shell).

### 2. Entrar (`/aluno/entrar`, POST)
*   **Formulário**: `email` (normalizado para minúsculas) + `senha`.
*   **Proteção CSRF**: token renderizado no formulário.
*   **Fluxo**: `entrar_com_senha` (Supabase Auth) → o SDK encadeia o JWT do usuário nas queries; busca a linha do aluno via `usuarios.auth_id`; conta Auth sem perfil (ex.: perfil apagado) tem o perfil recriado na hora; por fim `login_user` (Flask-Login) e refresh token guardado na sessão.
*   **Falha**: credenciais inválidas → flash "E-mail ou senha incorretos."

### 3. Criar Conta (`/aluno/criar`, POST)
*   **Formulário**: `username` (como quer ser chamado) + `email` + `senha` (mínimo 8 caracteres, validado antes de chamar o Auth).
*   **Fluxo**: `criar_conta_auth` (Supabase Auth) → cria a linha de perfil `usuarios` (`auth_id`, `username`, `email`) → login direto.
*   **"Confirm email" ligado** (dashboard do Auth): a conta nasce sem sessão — o aluno recebe flash pedindo confirmação pelo e-mail e entra depois.
*   **E-mail já cadastrado**: flash orientando login ou recuperação de senha.

### 4. Recuperar Senha (`/aluno/esqueci`, POST)
*   Dispara o e-mail de reset do Supabase Auth (`reset_password_for_email`) — requer SMTP configurado no dashboard do projeto (Zoho). Mensagem neutra: "se este e-mail tiver conta, enviamos o link".

### 5. Encerramento de Sessão (`/logout`)
*   Limpa a identidade do client Supabase (`sair_auth`), executa `logout_user()` e remove da sessão Flask **apenas as chaves não administrativas** (preserva `admin_*`), incluindo o `auth_refresh_token`.
*   Redireciona para a página de apresentação (`aluno.index`).

## Histórico do Modelo

| Era | Modelo |
|---|---|
| Web/SaaS (extinto) | E-mail + senha na própria tabela `usuarios` (hash local), verificação de e-mail, recuperação por token. |
| Desktop passwordless (extinto) | Auto-login local sem senha — origem do bug "um usuário novo a cada login" (`.limit(1)` na tabela compartilhada + secret key aleatória a cada boot). |
| **Atual** | Supabase Auth (hashes ficam em `auth.users`, invisíveis ao anon) + RLS por dono (`auth.uid()`) + sessão lembrada via refresh token. |

> **Colunas de banco extintas** (migration `drop_auth_columns_desktop_no_password`): `email_verificado`, `codigo_verificacao`, `token_recuperacao`, `expiracao_token`. As colunas `password_hash`, `session_token` e `totp_secret` vivem na tabela `admins` (migration `split_usuarios_admins`) — a tabela `usuarios` é exclusiva dos alunos (com a nova coluna `auth_id`).