# Blueprint `auth` — Login com E-mail e Senha (Supabase Auth)

> [!IMPORTANT]
> **Autenticação real por usuário.** Cada aluno tem conta própria (e-mail + senha) no **Supabase Auth** — o progresso fica na nuvem e acompanha o usuário em qualquer máquina.
> O vínculo é feito por `usuarios.auth_id` (migration `auth_usuario_e_policies`); a escrita no banco exige, além do header `x-app-token`, que o `auth.uid()` do JWT bata com o dono da linha (RLS por dono).
> O painel administrativo mantém o próprio login (senha + 2FA, tabela `admins`; ver `docs/rotas/admin.md` no repo do painel).

## Rotas Ativas

### 1. Tela de Login / Sessão Eterna (`/aluno/login`, GET)
*   **Portão de entrada**: a raiz `/` (ex-landing de apresentação, aposentada) redireciona para esta tela; alunos logados seguem direto à área do aluno.
*   **Redirecionamento de autenticados**: alunos logados vão direto à área do aluno.
*   **Sessão eterna (desktop)**: o login grava o refresh token na sessão Flask (`auth_refresh_token`) e marca a sessão como **permanente** (`session.permanent = True` no `_entrar_flask` → cookie com data de expiração de 10 anos, `PERMANENT_SESSION_LIFETIME` no `app.py`). **Sem a permanência, o Chromium do Electron descarta o cookie de sessão ao fechar o app** e o aluno precisaria logar a cada abertura. Com ela: reabrir o app entra direto no painel, sem redigitar a senha; o perfil é reconstituído via `usuarios.auth_id`. Refresh inválido/expirado → token descartado e tela normal.
*   **Rotação persistida + renovação proativa**: o `before_request` de `app.py` reaplica o JWT do aluno logado quando o processo Flask reinicia (o client global perde a sessão em memória; o refresh token vive no cookie persistido pela `FLASK_SECRET_KEY` fixa do shell) e **grava de volta o NOVO refresh token de cada rotação** — o Supabase tem refresh token rotation ativo (cada refresh emite um token novo e invalida o anterior; sem essa persistência o aluno seria deslogado no boot seguinte). Quando o access token está a menos de 2 minutos de expirar, ele é **renovado proativamente**. A guarda do `before_request` é a chave `_user_id` da sessão Flask (a mesma que o Flask-Login usa para chamar o `user_loader`) — **não** `current_user.is_authenticated`, que dispararia o `load_user` antes da restauração e barraria o usuário logado com 302 no 1º request pós-boot. Como redes de segurança, o próprio `load_user` repete o self-heal (perfil vazio → restaura pelo refresh token → reconsulta uma vez) e a tela de login também restaura. A única forma de encerrar a sessão é o botão **Sair** (`/logout`).

### 2. Entrar (`/aluno/entrar`, POST)
*   **Formulário**: `email` (normalizado para minúsculas) + `senha`.
*   **Proteção CSRF**: token renderizado no formulário.
*   **Fluxo**: `entrar_com_senha` (Supabase Auth) → o SDK encadeia o JWT do usuário nas queries; busca a linha do aluno via `usuarios.auth_id`; conta Auth sem perfil (ex.: perfil apagado ou **aluno legado pré-Auth sem vínculo**) dispara `_criar_perfil`: primeiro tenta **adotar a linha legada de mesmo e-mail** (`UPDATE ... WHERE auth_id IS NULL` — migrations `relink_perfil_legado_usuarios` + `relink_visibilidade_select_legado`; o RLS só libera quando o e-mail CONFIRMADO do JWT bate com o da linha) e, só se não houver, cria linha nova — com sufixo `_hex` no username se colidir (padrão do cadastro antigo do site); por fim `login_user` (Flask-Login) e refresh token guardado na sessão.
*   **Falha**: credenciais inválidas → flash "E-mail ou senha incorretos."

### 3. Criar Conta (`/aluno/criar`, POST)
*   **Formulário**: `username` (como quer ser chamado) + `email` + `senha` (mínimo 8 caracteres, validado antes de chamar o Auth) + `confirmar_senha` — os dois campos precisam conferir (validação inline no browser e no servidor, antes do Auth, para evitar conta criada com senha digitada errada).
*   **Fluxo**: `criar_conta_auth` (Supabase Auth) → `_criar_perfil` (mesmo helper do login: adota a linha legada de mesmo e-mail se existir; sufixo `_hex` no username se colidir) → login direto.
*   **"Confirm email" ligado** (dashboard do Auth): a conta nasce sem sessão — o aluno recebe flash pedindo confirmação pelo e-mail e entra depois. O link do e-mail redireciona para a **página pública** (`site/`, GitHub Pages — ver seção 6): a confirmação acontece no servidor do Supabase ao clicar.
*   **E-mail já cadastrado**: flash orientando login ou recuperação de senha.

### 4. Recuperar Senha (`/aluno/esqueci`, POST)
*   Dispara o e-mail de reset do Supabase Auth (`reset_password_for_email`) — requer SMTP configurado no dashboard do projeto (Zoho). Mensagem neutra: "se este e-mail tiver conta, enviamos o link". O link redireciona para a **página pública** (`site/`), onde o aluno define a nova senha direto no navegador.

### 5. Encerramento de Sessão (`/logout`)
*   Limpa a identidade do client Supabase (`sair_auth` — **revoga o refresh token no servidor**), executa `logout_user()` e remove da sessão Flask **apenas as chaves não administrativas** (preserva `admin_*`), incluindo o `auth_refresh_token`.
*   Com a sessão eterna do desktop, este é o **único** caminho de deslogar (o cookie não expira sozinho): reabrir o app após o logout mostra a tela de login normal.
*   Redireciona para a tela de login (`auth.login_aluno`) — a ex-página de apresentação foi aposentada com o fim do modelo pago.

### 6. Página Pública de Confirmação (`site/` → GitHub Pages)
O app é local (`127.0.0.1:5000`), então os links dos e-mails do Supabase Auth (confirmação de cadastro e recuperação de senha) não podem redirecionar para a própria máquina. Eles apontam para uma **página estática publicada no GitHub Pages** (`https://thierry-moreira.github.io/gabaritei-questoes/`, fonte em `site/`, branch `gh-pages`):
*   O clique no link valida a conta **no servidor do Supabase**; a página informa o aluno ("E-mail confirmado! Volte ao aplicativo").
*   Link expirado/inválido → mensagem traduzida + form de **reenvio** do e-mail de confirmação (`auth.resend` na própria página).
*   Recuperação de senha → form de **nova senha** direto na página (`auth.updateUser`), com descarte da sessão ao final e limpeza imediata de tokens da URL.
*   Os helpers `criar_conta_auth`/`pedir_reset_senha` (`banco_dados_aluno.py`, `URL_POS_EMAIL`) enviam `email_redirect_to`/`redirect_to` explícitos; a URL também é o **Site URL** e precisa estar na allow list **Redirect URLs** do dashboard (Authentication → URL Configuration).
*   Publicação e detalhes: `site/README.md`.

## Histórico do Modelo

| Era | Modelo |
|---|---|
| Web/SaaS (extinto) | E-mail + senha na própria tabela `usuarios` (hash local), verificação de e-mail, recuperação por token. |
| Desktop passwordless (extinto) | Auto-login local sem senha — origem do bug "um usuário novo a cada login" (`.limit(1)` na tabela compartilhada + secret key aleatória a cada boot). |
| **Atual** | Supabase Auth (hashes ficam em `auth.users`, invisíveis ao anon) + RLS por dono (`auth.uid()`) + sessão lembrada via refresh token. |

> **Colunas de banco extintas** (migration `drop_auth_columns_desktop_no_password`): `email_verificado`, `codigo_verificacao`, `token_recuperacao`, `expiracao_token`. As colunas `password_hash`, `session_token` e `totp_secret` vivem na tabela `admins` (migration `split_usuarios_admins`) — a tabela `usuarios` é exclusiva dos alunos (com a nova coluna `auth_id`).

> **Perfis legados** (eras web/SaaS e desktop passwordless): as linhas de `usuarios` criadas antes do Supabase Auth ficaram com `auth_id = NULL`. No 1º login com e-mail + senha, elas são **adotadas** pelo dono do e-mail confirmado (re-link via RLS — ver fluxo do `/aluno/entrar`), sem duplicação do aluno nem colisão de username/e-mail (causa do 500 corrigido em out/2026).