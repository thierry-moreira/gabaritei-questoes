# Documentação Técnica: `banco_dados.py` e `banco_dados_aluno.py`

## Descrição Geral
O projeto mantém **dois clientes Supabase**, um por aplicação — a mesma ponte de comunicação (PostgreSQL via PostgREST), chaves diferentes:

| Módulo | Aplicação | Chave (`.env`) | Papel |
|---|---|---|---|
| `banco_dados.py` | Painel administrativo (`app_admin.py`) | `SUPABASE_KEY` (**service_role**) | Bypass total de RLS — uso interno, jamais distribuído |
| `banco_dados_aluno.py` | App do aluno (`app.py`, futuro Electron) | `SUPABASE_ANON_KEY` (**anon**) | Pública por definição — protegida pelas policies RLS |

Ambos exportam a instância global com o **mesmo nome `supabase`**, de propósito: rotas e testes (patches `@patch('rotas.X.supabase')`) não mudam ao trocar a origem do import.

> [!CAUTION]
> **A `service_role` (`SUPABASE_KEY`) jamais pode ser embarcada no app do aluno/bundle Electron.** Ela dá bypass total de RLS — quem a extrair do binário teria acesso destrutivo ao banco. O app do aluno usa exclusivamente `banco_dados_aluno.py`.

---

## Políticas RLS (migration `rls_policies_aluno`)
Todas as tabelas têm RLS habilitado; as policies liberam ao papel `anon` exatamente o que o app do aluno usa:

- **Conteúdo** (12 tabelas: `questoes`, `alternativas_questao`, `textos_base`, `provas_origem`, `materias`, `topicos`, `subtopicos`, `orgaos`, `cargos`, `bancas`, `niveis_escolaridade`, `prompts_materias`): **SELECT** — em `questoes`/`alternativas_questao` filtrado a `status='publicada'` (pendentes invisíveis fora do painel; migration `security_hardening_p1`).
- **Cache IA** (`ia_cache_estudo`, `explicacoes_ia`): **SELECT + INSERT**. A tabela de stats anônimas `historico_respostas_anonimo` é legado da era web — o app do aluno não insere mais, mas os dados históricos são preservados.
- **Feedbacks** (`feedbacks_questoes`): **SELECT + INSERT com token** (o SELECT é necessário porque o `INSERT ... RETURNING` do PostgREST aplica as SELECT policies às linhas retornadas; os relatos são anônimos, sem `id_usuario`). A **exclusão** continua exclusiva do painel/service.
- **Denúncias** (`reports_comentarios`, migration `reports_comentarios_denuncias`): **INSERT e DELETE apenas do dono** — `eh_app_aluno() AND eh_dono_do_aluno(id_usuario)`; **sem SELECT para o app do aluno** (a triagem é humana no painel admin, via `service_role`). PK composta `(id_comentario, id_usuario)` impede denúncia duplicada (23505 → o app responde 409 amigável); FK `ON DELETE CASCADE` para `comentarios_questao` — comentário excluído no painel leva as denúncias junto. Substitui a antiga moderação por IA: a blocklist local (`utils.verificar_texto_improprio`) segue como primeira barreira na publicação.
- **Dados do aluno** (16 tabelas: `usuarios`, `historico_respostas`, `comentarios_questao`, `flashcards`, `flashcard_categorias`, `resumos_estudo`, `cadernos`, `caderno_questoes`, `filtros_salvos`, `simulados`, `simulados_questoes`, `simulados_resultados`, `editais_*`): **SELECT livre** (linter isenta; dados de estudo não são secretos — *exceção*: as 3 tabelas de progresso de edital, ver abaixo) + **INSERT/UPDATE/DELETE exigem o header `x-app-token`** (migration `rls_header_app_aluno`) — a função `public.eh_app_aluno()` compara o header com o token de app, que vive apenas no binário do aluno/`.env` de dev — **e, desde a migration `auth_usuario_e_policies`, também a identidade do dono**.

**Camada de dono — Auth por usuário** (migrations `auth_usuario_e_policies` + `editais_leitura_por_dono` + `policies_para_authenticated`): cada aluno agora autentica no **Supabase Auth** (e-mail + senha) e `usuarios.auth_id` guarda o vínculo com `auth.users`. O SDK encadeia o JWT do usuário em todas as queries; como o JWT carrega `role=authenticated`, todas as policies foram regeneradas para `TO anon, authenticated`. Toda policy de escrita dos dados do aluno passou a exigir `eh_app_aluno() AND eh_dono_do_aluno(id_usuario)` (em `simulados` a coluna é `id_criador`; em `simulados_questoes` o dono é herdado do simulado) — resultado: mesmo que alguém extraia anon key **e** APP_TOKEN do binário, não escreve dados de outro aluno. O INSERT em `usuarios` usa `WITH CHECK (auth.uid() = auth_id)` (auto-cadastro da própria conta). As 3 tabelas de progresso de edital (`editais_materias`, `editais_topicos`, `editais_progresso`) ganharam `id_usuario` (FK CASCADE — eram herança do design single-user, sem dono) e leitura exclusiva do dono (não alimentam rankings). `feedbacks_questoes`, `historico_respostas_anonimo`, `ia_cache_estudo` e `explicacoes_ia` permanecem token-only (sem dono, anônimas por design).

**Re-link de perfis legados** (migrations `relink_perfil_legado_usuarios` + `relink_visibilidade_select_legado`): alunos das eras anteriores ao Supabase Auth ficaram com `auth_id = NULL`. No 1º login pós-Auth, o app tenta `UPDATE ... WHERE auth_id IS NULL` e o RLS só libera a linha quando o e-mail CONFIRMADO do JWT (`auth.jwt()->>'email'`, comparado com `lower()` dos dois lados) bate com o da linha, junto do header `x-app-token`. Como o UPDATE do Postgres exige que a linha também seja visível às policies de SELECT, a policy `anon_le_dados_aluno` de `usuarios` ganhou a cláusula OR do legado (a própria linha, ainda sem vínculo, visível ao dono do e-mail do JWT). Isolamento verificado: tentar adotar a linha de outro e-mail afeta 0 linhas.
- **`admins` e `logs_admin`**: **sem policies e `REVOKE ALL` de `anon`/`authenticated`** — deny-all de RLS + grant revogado (nem descobertas via GraphQL; qualquer acesso devolve `permission denied`).
- **Storage**: o bucket `imagens_questoes` é **público com public URLs diretas** no app (a policy SELECT de `storage.objects` foi removida — o signed URL de 60s não protegia nada num bucket público; migration `rls_header_app_aluno`). O **upload é exclusivo do painel** (`TO service_role`), com limite de 5MB e apenas mimes de imagem (png/jpeg/webp/gif).
- As views (`view_questoes_completa`, `view_taxa_acerto_questoes`) rodam com `security_invoker=on` — respeitam o RLS das tabelas base.

**Escrita com token de app** (migration `rls_header_app_aluno`): todas as policies de escrita do aluno validam o header HTTP `x-app-token` contra a função `public.eh_app_aluno()` — o token (gerado com `secrets.token_hex(32)`) vive apenas no binário do Electron/`.env` de dev/`desktop/main.js`, no mesmo nível de segredo que a anon key. Resultado: extrair **só** a anon key pública já não permite mais escrever NADA (INSERT negado, UPDATE/DELETE 0 linhas) — vandalismo cross-user exige reverse-engineering do binário. Leitura das tabelas de dados continua livre (design; login é local). Rotação: regenerar o token e atualizar (migration da função + `.env` + `desktop/main.js`).

Limites conhecidos (sem servidor, irreversíveis): o conteúdo é raspável por quem extrair a anon key; quem extrair **anon key + token do binário** ainda pode escrever como outro `id_usuario` (isolamento per-usuário seguiria exigindo Supabase Auth silencioso — roadmap).

**Hardening de grants** (migration `security_hardening_p1`): além do RLS, `anon` perdeu `TRUNCATE` em todas as tabelas (RLS não se aplica a TRUNCATE), perdeu toda escrita nas 12 tabelas de conteúdo (só SELECT) e perdeu tudo em `admins`/`logs_admin` — defesa em profundidade contra qualquer regressão de policy.

**GraphQL desabilitado + advisor limpo** (migration `disable_graphql_move_trgm`): a extensão `pg_graphql` foi removida com CASCADE (o app nunca usou a API GraphQL; reversível com `create extension pg_graphql;`) e o `pg_trgm` foi movido do schema `public` para o `extensions` (o índice trinário de `textos_base` sobreviveu — índices referenciam a opclass por OID). Os achados restantes do Security Advisor são **design intencional**: `rls_enabled_no_policy` em `admins`/`logs_admin` (deny-all deliberado), `rls_policy_always_true` nas policies de escrita do aluno (consequência da ausência de identidade server-side — ver limites conhecidos) e o listing público do bucket `imagens_questoes` (a policy SELECT é exigida pelos `create_signed_url` do app). Chaves públicas: apenas a `anon` legacy permanece habilitada.

---

## Configurações de Rede (Resiliência de Conexão)
Para lidar de forma robusta com instabilidades de rede — incluindo oscilações de conexão com a internet típicas do uso local/desktop — o cliente Supabase é configurado explicitamente utilizando a classe `SyncClientOptions`:

- **Timeout do Cliente PostgREST**: Configurado para um limite estrito de 30 segundos (`postgrest_client_timeout=30`). Essa parametrização impede que requisições extremamente demoradas ou em gargalo de infraestrutura bloqueiem permanentemente as threads/workers síncronas do servidor Flask.
- **Cabeçalho de Conexão (Header Connection)**: Configurado como `"Connection": "close"`. Esta estratégia desativa o keep-alive do HTTP nas requisições da API do Supabase, evitando problemas crônicos de "Broken Pipe", vazamento de conexões abertas ou conexões em estado zumbi em proxies de infraestrutura que reciclam sessões de rede de forma intermitente.

---

## Variáveis de Ambiente e Trava Fail-Fast
O projeto depende diretamente de três chaves armazenadas de maneira segura no arquivo de configuração `.env` (ou variáveis de sistema na plataforma de hospedagem):

1.  **`SUPABASE_URL`**: O endpoint HTTP REST exclusivo do seu projeto Supabase.
2.  **`SUPABASE_KEY`**: Chave **service_role** — exclusiva do painel administrativo (`banco_dados.py`, bypass de RLS).
3.  **`SUPABASE_ANON_KEY`**: Chave **anon** — usada pelo app do aluno (`banco_dados_aluno.py`, protegida por RLS).

> [!CAUTION]
> **Mecanismo de Segurança Fail-Fast (Parada Imediata)**:
> Se as chaves `SUPABASE_URL` ou `SUPABASE_KEY` não forem encontradas durante a importação do módulo, a aplicação lançará imediatamente uma exceção `ValueError` de erro crítico, interrompendo o ciclo de inicialização do servidor. Isso evita que a aplicação entre em execução em estado inconsistente ou que falhe silenciosamente em tempo de execução para os usuários finais.

---

## Uso no Código
Ambos os módulos resultam em uma instância global chamada `supabase`:

```python
# Rotas do painel admin (service_role — bypass de RLS)
from banco_dados import supabase

# Rotas do app do aluno (anon — protegida por RLS)
from banco_dados_aluno import supabase

# Exemplo de busca de dados
resultado = supabase.table("usuarios").select("*").execute()
```

---

## Backup local soberano (`backup_banco.py`)
O plano **free** do Supabase retém backups por ~7 dias apenas — para vandalismo ou erro grave não haver recuperação além dessa janela, o projeto mantém uma cópia independente:

- **Uso**: `python backup_banco.py` → baixa as 34 tabelas (service_role, paginação de 1000 com verificação de contagem) + os arquivos do bucket `imagens_questoes` para `backup_dados/<timestamp>/` (gitignored).
- **Integridade**: cada tabela é comparada com o `count` do banco — divergência aborta o script com erro (exit ≠ 0, detectável pelo Task Scheduler).
- **Agendamento**: a task **"Gabaritei Backup"** já está criada no Windows (diária às 09:00, com `StartWhenAvailable` — se o PC estiver desligado no horário, roda assim que ligar). Teste real validado: disparo manual retornou `LastTaskResult=0`. Para recriar em outra máquina: `Register-ScheduledTask -TaskName "Gabaritei Backup" -Action (New-ScheduledTaskAction -Execute "<venv>\Scripts\python.exe" -Argument '"backup_banco.py"' -WorkingDirectory "<projeto>") -Trigger (New-ScheduledTaskTrigger -Daily -At 09:00)`.
- ⚠️ A pasta contém dados sensíveis (hash de senha/TOTP dos admins, e-mails) — manter apenas local.

---

## Práticas de Resiliência de Acesso a Dados
Embora a instância `supabase` esteja globalmente disponível, é considerada uma excelente prática **não invocá-la diretamente para escritas ou consultas cruciais em rotas**. 

Em vez disso, as operações devem ser empacotadas utilizando a função utilitária `safe_execute` localizada em `utils.py`. A função `safe_execute` adiciona uma camada inteligente de retentativa automática (com recuo exponencial e tratativas de exceções gerais) para tolerar falhas pontuais e momentâneas de rede ou concorrência de requisições no Supabase.
