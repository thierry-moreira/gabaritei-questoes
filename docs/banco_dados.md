# Documentação Técnica: banco de dados do app do aluno (`banco_dados_aluno.py`)

## Descrição Geral
Este repositório contém apenas o **app do aluno**. O cliente Supabase do aluno é `banco_dados_aluno.py` — PostgreSQL via PostgREST com a **ANON key pública** e o header `x-app-token`. O painel administrativo vive em um repositório privado separado (`gabaritei-admin`) e usa o próprio cliente com **service_role**, fora deste escopo.

| Módulo | Aplicação | Chave (`.env`) | Papel |
|---|---|---|---|
| `banco_dados_aluno.py` | App do aluno (`app.py` + Electron) | `SUPABASE_ANON_KEY` (**anon**) + `APP_TOKEN` | Pública por definição — protegida pelas policies RLS; escrita exige token **e** dono |
| `banco_dados.py` (repo separado) | Painel administrativo (`app_admin.py`) | `SUPABASE_KEY` (**service_role**) | Bypass total de RLS — uso interno, jamais distribuído |

O módulo exporta a instância global `supabase` (mesmo nome usado nos patches `@patch('rotas.X.supabase')` e nos testes).

> [!CAUTION]
> **A `service_role` (`SUPABASE_KEY`) jamais pode ser embarcada no app do aluno/bundle Electron.** Ela dá bypass total de RLS — quem a extrair do binário teria acesso destrutivo ao banco. O app do aluno usa exclusivamente `banco_dados_aluno.py`.

---

## Políticas RLS (migration `rls_policies_aluno`)
Todas as tabelas têm RLS habilitado; as policies liberam ao papel `anon` exatamente o que o app do aluno usa:

- **Conteúdo** (12 tabelas: `questoes`, `alternativas_questao`, `textos_base`, `provas_origem`, `materias`, `topicos`, `subtopicos`, `orgaos`, `cargos`, `bancas`, `niveis_escolaridade`, `prompts_materias`): **SELECT** — em `questoes`/`alternativas_questao` filtrado a `status='publicada'` (pendentes invisíveis fora do painel; migration `security_hardening_p1`).
- **Cache IA** (`ia_cache_estudo`, `explicacoes_ia`): **SELECT + INSERT**. A tabela de stats anônimas `historico_respostas_anonimo` é legado da era web — o app do aluno não insere mais, mas os dados históricos são preservados.
- **Feedbacks** (`feedbacks_questoes`): **SELECT + INSERT com token** (o SELECT é necessário porque o `INSERT ... RETURNING` do PostgREST aplica as SELECT policies às linhas retornadas; os relatos são anônimos, sem `id_usuario`). A **exclusão** continua exclusiva do painel/service.
- **Denúncias** (`reports_comentarios`, migration `reports_comentarios_denuncias`): **INSERT e DELETE apenas do dono** — `eh_app_aluno() AND eh_dono_do_aluno(id_usuario)`; **sem SELECT para o app do aluno** (a triagem é humana no painel admin, via `service_role`). PK composta `(id_comentario, id_usuario)` impede denúncia duplicada (23505 → o app responde 409 amigável); FK `ON DELETE CASCADE` para `comentarios_questao` — comentário excluído no painel leva as denúncias junto. Substitui a antiga moderação por IA: a blocklist local (`utils.verificar_texto_improprio`) segue como primeira barreira na publicação.
- **Dados do aluno** (16 tabelas: `usuarios`, `historico_respostas`, `comentarios_questao`, `flashcards`, `flashcard_categorias`, `resumos_estudo`, `cadernos`, `caderno_questoes`, `filtros_salvos`, `simulados`, `simulados_questoes`, `simulados_resultados`, `editais_*`): **SELECT livre** (decisão de design do modelo local — *exceção*: as 3 tabelas de progresso de edital, ver abaixo) + **INSERT/UPDATE/DELETE exigem o header `x-app-token`** (migration `rls_header_app_aluno`) — a função `public.eh_app_aluno()` compara o header com o token de app, que vive apenas no binário do aluno/`.env` de dev — **e, desde a migration `auth_usuario_e_policies`, também a identidade do dono**.

**Camada de dono — Auth por usuário** (migrations `auth_usuario_e_policies` + `editais_leitura_por_dono` + `policies_para_authenticated`): cada aluno agora autentica no **Supabase Auth** (e-mail + senha) e `usuarios.auth_id` guarda o vínculo com `auth.users`. O SDK encadeia o JWT do usuário em todas as queries; como o JWT carrega `role=authenticated`, todas as policies foram regeneradas para `TO anon, authenticated`. Toda policy de escrita dos dados do aluno passou a exigir `eh_app_aluno() AND eh_dono_do_aluno(id_usuario)` (em `simulados` a coluna é `id_criador`; em `simulados_questoes` o dono é herdado do simulado) — resultado: mesmo que alguém extraia anon key **e** APP_TOKEN do binário, não escreve dados de outro aluno. O INSERT em `usuarios` usa `WITH CHECK (auth.uid() = auth_id)` (auto-cadastro da própria conta). As 3 tabelas de progresso de edital (`editais_materias`, `editais_topicos`, `editais_progresso`) ganharam `id_usuario` (FK CASCADE — eram herança do design single-user, sem dono) e leitura exclusiva do dono (não alimentam rankings). `feedbacks_questoes`, `historico_respostas_anonimo`, `ia_cache_estudo` e `explicacoes_ia` permanecem token-only (sem dono, anônimas por design).

**Re-link de perfis legados** (migrations `relink_perfil_legado_usuarios` + `relink_visibilidade_select_legado`): alunos das eras anteriores ao Supabase Auth ficaram com `auth_id = NULL`. No 1º login pós-Auth, o app tenta `UPDATE ... WHERE auth_id IS NULL` e o RLS só libera a linha quando o e-mail CONFIRMADO do JWT (`auth.jwt()->>'email'`, comparado com `lower()` dos dois lados) bate com o da linha, junto do header `x-app-token`. Como o UPDATE do Postgres exige que a linha também seja visível às policies de SELECT, a policy `anon_le_dados_aluno` de `usuarios` ganhou a cláusula OR do legado (a própria linha, ainda sem vínculo, visível ao dono do e-mail do JWT). Isolamento verificado: tentar adotar a linha de outro e-mail afeta 0 linhas.
- **`admins` e `logs_admin`**: **sem policies e `REVOKE ALL` de `anon`/`authenticated`** — deny-all de RLS + grant revogado (nem descobertas via GraphQL; qualquer acesso devolve `permission denied`).
- **Storage**: o bucket `imagens_questoes` é **público com public URLs diretas** no app (a policy SELECT de `storage.objects` foi removida — o signed URL de 60s não protegia nada num bucket público; migration `rls_header_app_aluno`). O **upload é exclusivo do painel** (`TO service_role`), com limite de 5MB e apenas mimes de imagem (png/jpeg/webp/gif).
- As views (`view_questoes_completa`, `view_taxa_acerto_questoes`) rodam com `security_invoker=on` — respeitam o RLS das tabelas base.

**Escrita com token de app** (migration `rls_header_app_aluno`): todas as policies de escrita do aluno validam o header HTTP `x-app-token` contra a função `public.eh_app_aluno()` — o token (gerado com `secrets.token_hex(32)`) vive apenas no binário do Electron/`.env` de dev/`desktop/token.local.js`, no mesmo nível de segredo que a anon key. Resultado: extrair **só** a anon key pública já não permite escrever nada (INSERT negado, UPDATE/DELETE 0 linhas) — e, desde `auth_usuario_e_policies`, nem o token sozinho basta: a escrita também exige o JWT do dono. Leitura das tabelas de dados de estudo continua liberada pelo desenho atual (exceto as 3 tabelas de progresso de edital). Rotação: regenerar o token e atualizar a migration da função, o `.env` de dev e `desktop/token.local.js`.

Limites conhecidos (sem servidor, irreversíveis): o conteúdo é raspável por quem extrair a anon key; a leitura dos dados de estudo é liberada pelo desenho atual (privacidade entre alunos não é garantida em `SELECT`, com exceção das 3 tabelas de edital); quem extrair **anon key + APP_TOKEN + um JWT válido** ainda age como aquele aluno, mas não escreve em nome de outro `id_usuario`. A `service_role` continua fora do app.

**Hardening de grants** (migration `security_hardening_p1`): além do RLS, `anon` perdeu `TRUNCATE` em todas as tabelas (RLS não se aplica a TRUNCATE), perdeu toda escrita nas 12 tabelas de conteúdo (só SELECT) e perdeu tudo em `admins`/`logs_admin` — defesa em profundidade contra qualquer regressão de policy.

**GraphQL desabilitado + advisor limpo** (migration `disable_graphql_move_trgm`): a extensão `pg_graphql` foi removida com CASCADE (o app nunca usou a API GraphQL; reversível com `create extension pg_graphql;`) e o `pg_trgm` foi movido do schema `public` para o `extensions` (o índice trinário de `textos_base` sobreviveu — índices referenciam a opclass por OID). Achados restantes do Security Advisor que são **design intencional**: `rls_enabled_no_policy` em `admins`/`logs_admin` (deny-all deliberado) e o listing público do bucket `imagens_questoes` (as public URLs são usadas pelo app). As policies de escrita atuais exigem `eh_app_aluno() AND eh_dono_do_aluno(...)`; qualquer achado de policy permissiva deve ser reavaliado no dashboard. Chaves públicas: apenas a `anon` legacy permanece habilitada.

---

## Configurações de Rede (Resiliência de Conexão)
Para lidar de forma robusta com instabilidades de rede — incluindo oscilações de conexão com a internet típicas do uso local/desktop — o cliente Supabase é configurado explicitamente utilizando a classe `SyncClientOptions`:

- **Timeout do Cliente PostgREST**: Configurado para um limite estrito de 30 segundos (`postgrest_client_timeout=30`). Essa parametrização impede que requisições extremamente demoradas ou em gargalo de infraestrutura bloqueiem permanentemente as threads/workers síncronas do servidor Flask.
- **Cabeçalho de Conexão (Header Connection)**: Configurado como `"Connection": "close"`. Esta estratégia desativa o keep-alive do HTTP nas requisições da API do Supabase, evitando problemas crônicos de "Broken Pipe", vazamento de conexões abertas ou conexões em estado zumbi em proxies de infraestrutura que reciclam sessões de rede de forma intermitente.

---

## Variáveis de Ambiente e Trava Fail-Fast
O `banco_dados_aluno.py` depende de três variáveis no `.env` (ou no ambiente do processo spawnado pelo Electron):

1.  **`SUPABASE_URL`**: endpoint HTTP REST do projeto Supabase.
2.  **`SUPABASE_ANON_KEY`**: chave **anon** — pública por design, protegida pelas policies RLS.
3.  **`APP_TOKEN`**: segredo de app (gerado com `secrets.token_hex(32)`), enviado em **todas as requisições ao PostgREST** no header `x-app-token`; exigido pelas policies de escrita.

O app como um todo também usa **`FLASK_SECRET_KEY`** (sessão), **`GABARITEI_LOCAL_DIR`** (SQLite + DPAPI da chave BYOK; no Electron aponta para o `userData`) e, opcionalmente, **`TRUSTED_PROXIES`** (ProxyFix).

> [!CAUTION]
> **Mecanismo de Segurança Fail-Fast (Parada Imediata)**:
> Se `SUPABASE_URL` ou `SUPABASE_ANON_KEY` faltarem na importação, o módulo lança `ValueError` e interrompe a inicialização. O mesmo acontece se `APP_TOKEN` não estiver configurado — sem ele, nenhuma escrita do aluno passa no RLS. Isso evita subir a aplicação em estado inconsistente.

---

## Uso no Código
O módulo exporta a instância global `supabase` e os helpers de Auth:

```python
# Rotas do app do aluno (anon + x-app-token — protegida por RLS)
from banco_dados_aluno import supabase

# Auth (Supabase Auth): login, cadastro, refresh e reset de senha
from banco_dados_aluno import (
    entrar_com_senha, criar_conta_auth, restaurar_sessao,
    sessao_atual, sair_auth, pedir_reset_senha,
)

# Exemplo de busca de dados
resultado = supabase.table("usuarios").select("*").execute()
```

O cliente admin (`banco_dados.py`, service_role) **não existe neste repositório** — ele pertence ao repo privado `gabaritei-admin`.

---

## Práticas de Resiliência de Acesso a Dados
Embora a instância `supabase` esteja globalmente disponível, é considerada uma excelente prática **não invocá-la diretamente para escritas ou consultas cruciais em rotas**. 

Em vez disso, as operações devem ser empacotadas utilizando a função utilitária `safe_execute` localizada em `utils.py`. A função `safe_execute` adiciona uma camada de retentativa automática (até 3 tentativas, pausa fixa de `0.5` s e sem retry para erros determinísticos listados em `ERROS_SEM_RETRY`) para tolerar falhas pontuais e momentâneas de rede ou concorrência de requisições no Supabase.
