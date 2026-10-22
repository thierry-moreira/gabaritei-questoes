# Página Pública de Confirmação (GitHub Pages)

Página estática que recebe o **redirecionamento dos e-mails do Supabase Auth** — o app é local (`127.0.0.1:5000`), então o link de confirmação/recuperação não pode apontar para a própria máquina: o clique valida a conta **no servidor do Supabase** e cai aqui, informando o aluno.

**URL de produção:** `https://thierry-moreira.github.io/gabaritei-questoes/` (GitHub Pages, branch `gh-pages`).

## O que a página cobre

| Redirect recebido | Estado exibido |
|---|---|
| Limpo (confirmação de cadastro concluída) | "E-mail confirmado!" — orienta voltar ao app |
| `?error=...` (link expirado/inválido/`403`) | Mensagem traduzida + **form de reenvio** (`auth.resend`, rate-limited pelo GoTrue) |
| `?token&type=recovery` ou `#access_token&type=recovery` (recuperação de senha) | **Form de nova senha** (`auth.updateUser` direto na página) e confirmação |
| `?code=...` (fluxo PKCE, se o app um dia migrar) | Troca por sessão e segue o fluxo correspondente |

Extras de UX/segurança:
- Tokens são capturados em memória e a URL é **limpa imediatamente** (`history.replaceState`) — nada de `access_token` no histórico.
- Após salvar a nova senha, a sessão da página é descartada (`signOut`).
- Botão **"Entrar no aplicativo"** aparece se o app local responder em `http://127.0.0.1:5000` (probe `fetch` no-cors com timeout de 1,5s; localhost é permitido a partir de HTTPS nos browsers modernos).
- A anon key embutida é **pública por design** (a barreira é o RLS — ver `docs/banco_dados.md`).

## Como publicar (branch `gh-pages`)

A pasta `site/` deste repo é a fonte da página. Ela é publicada na raiz da branch `gh-pages`:

```bash
# 1. A partir da raiz do repo, após commitar mudanças em site/:
git subtree push --prefix=site origin gh-pages

# 2. No GitHub: Settings → Pages → Source: branch "gh-pages" (folder "/")
#    (se Pages já estiver ativo na gh-pages, o push republica sozinho)
```

## Configuração no Supabase (dashboard, uma vez)

**Authentication → URL Configuration:**
- **Site URL**: `https://thierry-moreira.github.io/gabaritei-questoes/`
- **Redirect URLs** (allow list): adicionar `https://thierry-moreira.github.io/gabaritei-questoes/`
  *(sem isso o GoTrue bloqueia o redirect com `403` — o app já envia `email_redirect_to`/`redirect_to` explícitos em `banco_dados_aluno.py`, mas a URL precisa estar na allow list)*

Os templates de e-mail do Auth seguem usando `{{ .ConfirmationURL }}` (padrão) — o redirect final já aponta para cá.

## Como testar localmente

Abra `site/index.html` direto no browser (ou `python -m http.server` dentro de `site/`) e simule os estados pela URL:
- `...index.html` → estado "E-mail confirmado"
- `...index.html?error=otp_expired&error_description=Token%20has%20expired` → estado de erro + reenvio
- `...index.html?token=invalido&type=recovery` → tentativa de sessão → cai no estado de erro (token inválido)

O fluxo completo (e-mail real → clique → redirect) só é testável com a página publicada e o SMTP (Zoho) configurado.

## Resolução de problemas

### "The custom domain ... is not properly formatted" (GitHub Pages)
Esse erro aparece quando a URL do site é colada no campo **Custom domain** (Settings → Pages). Esse campo é **apenas para domínios próprios comprados** (ex.: `meudominio.com`) — o endereço `thierry-moreira.github.io/...` é o padrão de projeto e **não deve** ser cadastrado lá. Configuração correta:
1. Settings → Pages → **Custom domain: vazio** (remova qualquer valor que chegou a ser salvo).
2. **Build and deployment → Source**: "Deploy from a branch" → branch **gh-pages**, pasta **/(root)**.
3. Salve — em ~1 min o site responde em `https://thierry-moreira.github.io/gabaritei-questoes/`.

### "Link inválido" ao reabrir o e-mail
Cada link do Auth é de **uso único** (one-time token): o primeiro clique já consome o token. Se o form de nova senha apareceu e você recarregou ou clicou no link de novo, o segundo clique retorna 403 ("One-time token not found") — comportamento normal do Supabase. Peça um novo e-mail e use **apenas o link novo**, sem reabrir o antigo.

### Erros que a página pode mostrar e o significado
- `Auth session missing!`: era um bug da página com a assinatura de `setSession` (corrigido em out/2026 — recebe um objeto `{access_token, refresh_token}`); se reaparecer, republicar a branch `gh-pages` com a versão atual de `site/`.
- `403`/`access_denied` sem `?error_description`: a URL da página provavelmente não está na allow list **Redirect URLs** do Supabase (Authentication → URL Configuration).
