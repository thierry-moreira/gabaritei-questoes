# Migrations do banco (Supabase)

Este diretório é a **fonte de verdade versionada** das mudanças de schema/RLS
aplicadas ao projeto Supabase `ivhuaevrrkrnagbqmnwc` (produção). O histórico
executado fica em `supabase_migrations.schema_migrations` e pode ser conferido
com `list_migrations` (MCP) ou no dashboard.

## Como aplicar

1. **Via MCP (recomendado):** use `apply_migration` com o conteúdo do arquivo
   `.sql` e um `name` curto (ex.: `rls_owner_only_e_conteudo_publico`). A
   ferramenta executa a migration em transação e registra a versão.
2. **Via SQL Editor:** cole o conteúdo do arquivo e execute. Os arquivos são
   idempotentes (`drop policy if exists` / `create or replace`) e podem ser
   reaplicados com segurança.
3. **Não** inclua `begin`/`commit` no arquivo de migration: o `apply_migration`
   já controla a transação. Scripts de teste (como `test_rls_f01.sql`) são a
   exceção — eles abrem transação e terminam em `rollback` de propósito.

Depois de aplicar uma migration que mexa em RLS/grants, rode os advisors de
segurança (`get_advisors` tipo `security`) e o teste correspondente.

## F-01 — RLS owner-only + conteúdo público

Arquivos:

| Arquivo | Papel |
|---|---|
| `rls_owner_only_e_conteudo_publico.sql` | Migration aplicada em produção (versão `20261103010532`). Recria o SELECT owner-only nas 16 tabelas de dados do aluno, endurece grants e cria as views/RPC de conteúdo público. |
| `test_rls_f01.sql` | Teste transacional (rollback) com dois usuários fictícios e `anon` sem JWT. 40 asserções. |

### O que a migration garante

- **Sem JWT (`anon`):** 0 linhas em `usuarios`, `historico_respostas`,
  `comentarios_questao`, `flashcards`, `flashcard_categorias`,
  `resumos_estudo`, `cadernos`, `caderno_questoes`, `filtros_salvos`,
  `simulados`, `simulados_questoes`, `simulados_resultados` e `editais_*`.
  O SELECT de `anon` é mantido (retorna 200 com 0 linhas) para que a
  restauração de sessão do `load_user` não quebre com `permission denied`;
  quem barra as linhas é a policy owner-only.
- **Com JWT:** cada aluno lê apenas as próprias linhas. `usuarios` usa
  `auth.uid() = auth_id`; as demais usam `eh_dono_do_aluno(id_usuario)`;
  `simulados` usa `id_criador`; `simulados_questoes` usa o dono do simulado pai.
- **Conteúdo público separado:** `view_comentarios_publicos`,
  `view_simulados_publicos`, `view_simulados_questoes_publicas` e a RPC
  `ranking_simulado(uuid)` expõem somente colunas/filtros públicos — nunca
  `id_usuario`, `id_criador`, `auth_id` ou e-mail. As views rodam como
  `postgres` (`security_invoker = false`) para atravessar o RLS owner-only;
  a segurança está no filtro e na lista explícita de colunas.
- **Defesa em profundidade:** `TRUNCATE` revogado de `anon` e `authenticated`
  (RLS não cobre TRUNCATE) e `INSERT/UPDATE/DELETE` revogados de `anon` nas
  tabelas de dados do aluno (escrita sempre sai com JWT).

### Como rodar o teste

1. Confirme que existe pelo menos uma questão com `status = 'publicada'`
   (o teste usa uma questão real somente como referência).
2. Execute `test_rls_f01.sql` no SQL Editor ou via MCP `execute_sql`.
3. Resultado esperado:

```json
{ "passou": true, "total": 40, "falhas": 0, "resultados": [ ... ] }
```

O script cria dois usuários fictícios com `auth_id` fixos, um simulado
público e um privado para cada, resultados, histórico e comentários; consulta
como `anon`, como o aluno A e como o aluno B; e termina com `ROLLBACK` — nada
fica no banco. Se `passou = false`, a coluna `resultados` mostra `esperado` x
`obtido` de cada asserção.

### Rollback manual

A migration é idempotente e não apaga dados de alunos. Se precisar reverter as
views/RPC públicas, remova os grants e os objetos criados no final do arquivo;
as policies owner-only devem permanecer (são o estado seguro esperado).

## F-07 — Feed público de comentários sem UUID do autor

Não exige migration adicional: o endpoint usa `view_comentarios_publicos`,
criada pela migration F-01 (`rls_owner_only_e_conteudo_publico.sql`), cuja
projeção não inclui `id_usuario`/`auth_id` e filtra questões publicadas. Em
`rotas/questao.py`, o `GET /api/comentarios/<id_questao>` seleciona e serializa
somente `id_comentario`, `nome_usuario`, `texto_comentario` e `criado_em`,
entrega 20 comentários por página (`?page=1`, `?page=2`, ...), rejeita offsets
acima de 10.000 e aplica rate limit de 60/minuto por IP. O teste de regressão
em `tests/test_aluno_questoes.py` verifica a projeção, o limite de página, o
offset e a configuração do rate limit; a interface expõe o botão para carregar
comentários anteriores.

## F-03 — Vínculo de questão só no próprio caderno

Arquivos:

| Arquivo | Papel |
|---|---|
| `caderno_questoes_dono_fk.sql` | Migration aplicada em produção (versão `20261103012334`). Torna `caderno_questoes.id_usuario` obrigatório, cria FK composta `(id_caderno, id_usuario) -> cadernos(id_caderno, id_usuario)` e reforça as policies de INSERT/UPDATE. |
| `test_f03.sql` | Teste transacional (rollback) com dois usuários: RLS + constraint + cascade. 12 asserções. |

### O que a migration garante

- **App:** `salvar_na_pasta` valida que `id_caderno` pertence a
  `current_user.id` antes do INSERT; caderno alheio/inexistente devolve **404**
  (sem revelar a existência) e não executa o INSERT.
- **Banco:** a FK composta amarra o dono do vínculo ao dono do caderno. Um
  INSERT/UPDATE com `id_usuario` divergente de `cadernos.id_usuario` falha com
  `23503`, inclusive via `service_role` (a FK não depende de RLS).
  `id_usuario` NULL falha com `23502`.
- **RLS:** as policies de INSERT/UPDATE de `caderno_questoes` também exigem
  `EXISTS (cadernos c WHERE c.id_caderno = ... AND c.id_usuario = ...)`. A
  subconsulta passa pela policy owner-only de `cadernos`, então um aluno não
  consegue nem spoofar o `id_usuario` do dono.
- **Cascade:** apagar o caderno continua removendo os vínculos
  (`ON DELETE CASCADE`); mover o dono do caderno propaga para os vínculos
  (`ON UPDATE CASCADE`).
- **Dados legados:** se existir vínculo cross-tenant ou `id_usuario` NULL, a
  migration **falha antes de alterar** a tabela com uma mensagem clara. Nada é
  apagado ou reescrito silenciosamente. Em produção (2026-11-03) havia 0
  cadernos e 0 vínculos, então a aplicação foi no-op. Para inspecionar um
  ambiente com conflito:

  ```sql
  select cq.id_caderno, cq.id_questao, cq.id_usuario,
         c.id_usuario as dono_do_caderno
  from public.caderno_questoes cq
  join public.cadernos c using (id_caderno)
  where cq.id_usuario is distinct from c.id_usuario;
  ```

  A decisão é explícita: remover o vínculo (poluição cross-tenant) ou
  reatribuir `id_usuario` ao dono do caderno. Rode o `test_f03.sql` depois.

### Como rodar o teste

1. Confirme que existem pelo menos **duas** questões com
   `status = 'publicada'` (a segunda isola a FK da PK composta).
2. Execute `test_f03.sql` no SQL Editor ou via MCP `execute_sql`.
3. Resultado esperado:

```json
{ "passou": true, "total": 12, "falhas": 0, "resultados": [ ... ] }
```

O token de `eh_app_aluno()` é lido em runtime de `pg_get_functiondef` para o
teste autenticado não gravar o segredo no repositório.

## F-04 — Resultado de simulado só em simulado público ou do próprio aluno

Arquivos:

| Arquivo | Papel |
|---|---|
| `simulados_resultados_visibilidade.sql` | Migration aplicada em produção (versão `20261103013458`). Reforça as policies de INSERT/UPDATE de `simulados_resultados` para exigir simulado público ou do próprio aluno. |
| `test_f04.sql` | Teste transacional (rollback) com dois usuários: INSERT/UPDATE cross-tenant, spoof de `id_usuario` e ranking. 13 asserções. |

### O que a correção garante

- **App (guard único):** `_simulado_do_usuario_ou_none` é a única porta de
  entrada de `fazer_simulado`, `corrigir_simulado`, `ver_ranking_simulado` e
  `baixar_pdf_simulado`. Ele retorna a linha somente quando o simulado é
  público ou pertence a `current_user.id`; simulado privado de outro aluno e
  simulado inexistente produzem a mesma resposta (flash + redirect), sem
  revelar que o ID existe.
- **Sem consulta indevida:** o guard roda **antes** de
  `_ids_questoes_do_simulado`, da consulta de gabarito
  (`alternativas_questao.is_correct`), do INSERT em `simulados_resultados` e
  da RPC `ranking_simulado`. O não-dono não chega a carregar questões,
  gabarito, resultados nem ranking.
- **Banco:** as policies de INSERT/UPDATE de `simulados_resultados` agora
  exigem `eh_app_aluno() AND eh_dono_do_aluno(id_usuario)` **e** que
  `id_simulado` exista em `view_simulados_publicos` (público) **ou** em
  `simulados` com `eh_dono_do_aluno(id_criador)` (privado do próprio aluno).
  Um INSERT/UPDATE cross-tenant via PostgREST/JWT falha com `42501`, mesmo
  que o cliente spoofe `id_usuario`.
- **Ranking:** a RPC `ranking_simulado` já libera o privado apenas para o
  criador; o guard da rota e a policy de `simulados_resultados` fecham as
  pontas de leitura e escrita. Isso cobre também os achados F-05 (ranking) e
  F-06 (PDF), que usam o mesmo guard.
- **Dados legados:** se existir resultado em simulado privado de outro aluno,
  a migration **falha antes de alterar** as policies com uma mensagem clara.
  Em produção (2026-11-03) havia 0 resultados, então a aplicação foi no-op.
  Para inspecionar:

  ```sql
  select r.id, r.id_simulado, r.id_usuario, s.id_criador
  from public.simulados_resultados r
  join public.simulados s on s.id = r.id_simulado
  where s.eh_privado is true
    and s.id_criador is distinct from r.id_usuario;
  ```

### Como rodar o teste

1. Execute `test_f04.sql` no SQL Editor ou via MCP `execute_sql`. Não depende
   de questões publicadas: usa apenas `usuarios`, `simulados` e
   `simulados_resultados`.
2. Resultado esperado:

```json
{ "passou": true, "total": 13, "falhas": 0, "resultados": [ ... ] }
```

O teste cria dois alunos e dois simulados privados (um por aluno) mais um
público, exercita INSERT/UPDATE como `authenticated` com JWT + `x-app-token`,
consulta o ranking dos dois lados e termina com `ROLLBACK` — nada fica no
banco. O token de `eh_app_aluno()` é lido em runtime de
`pg_get_functiondef`, como no F-03.

## F-11 — XSS armazenado em comentários (username e texto)

Arquivos:

| Arquivo | Papel |
|---|---|
| `comentarios_username_xss.sql` | Migration aplicada em produção (versão `20261103015702`). Adiciona CHECKs de formato em `usuarios.username` e `comentarios_questao.nome_usuario` e de tamanho/conteúdo em `comentarios_questao.texto_comentario`. |
| `test_f11.sql` | Teste transacional (rollback) com 8 asserções: allowlist de username, nome denormalizado e limites do texto. |

### O que a correção garante

- **App (saída):** o feed de comentários em `static/js/questoes_common.js`
  monta cada card com `createElement`/`textContent`/`createTextNode`; nome,
  texto e id do comentário nunca passam por `innerHTML` nem por template
  literal. Um payload `<img src=x onerror=...>` é exibido como texto e não
  executa.
- **App (entrada):** `utils.validar_username` normaliza espaços e aplica a
  allowlist de 2–30 caracteres (`letras`, números, espaço, ponto, hífen,
  sublinhado) no cadastro (`/aluno/criar`) e na edição de perfil
  (`/aluno/conta/`). `utils.validar_texto_comentario` rejeita texto vazio,
  acima de 1000 caracteres ou com caracteres de controle. O `id_questao` do
  payload precisa ser inteiro. Username legado fora do formato não é copiado
  para o comentário: o app grava `"Concurseiro"` como fallback.
- **App (perfil):** `_criar_perfil` usa o prefixo do e-mail como sugestão no
  primeiro login; o valor é sanitizado para a mesma allowlist e truncado
  antes de receber o sufixo `_hex`, então o username final nunca ultrapassa
  30 caracteres.
- **Banco:** as constraints `usuarios_username_formato`,
  `comentarios_nome_usuario_formato` e `comentarios_texto_valido` rejeitam
  com `23514` um INSERT/UPDATE direto via PostgREST que tente gravar HTML no
  nome, texto vazio/longo demais ou caracteres de controle. O **texto** do
  comentário continua armazenado como o aluno digitou (inclusive `<` e `>`
  legítimos); a defesa contra HTML no texto é a codificação de saída.
- **CSP (defesa em profundidade):** `app.py` passou a enviar
  `object-src 'none'`, `base-uri 'self'`, `frame-ancestors 'self'` e
  `form-action 'self'`. O `script-src` **mantém** `'unsafe-inline'` porque o
  app usa scripts/handlers inline em várias telas; removê-lo exigiria nonces
  em todos eles e migração dos `onclick`/`onload` para listeners — fica como
  endurecimento futuro, sem ser a defesa principal deste achado.
- **Dados legados:** a migration **falha antes de alterar** as tabelas se
  houver username ou comentário fora do padrão, com mensagem clara. Em
  produção (2026-11-03) havia 1 usuário e 0 comentários, todos dentro do
  padrão, então a aplicação foi no-op.

### Como rodar o teste

1. Confirme que existe pelo menos uma questão (o teste usa uma questão real
   apenas como referência para o INSERT de comentário).
2. Execute `test_f11.sql` no SQL Editor ou via MCP `execute_sql`.
3. Resultado esperado:

```json
{ "passou": true, "total": 8, "falhas": 0, "resultados": [ ... ] }
```

O teste cria um usuário e um comentário válidos, tenta os payloads proibidos
(HTML no username/nome, 31 caracteres, texto vazio, 1001 caracteres e
caractere de controle) e termina com `ROLLBACK` — nada fica no banco.

## Outras migrations

- `legislacao_busca.sql` — corpus/FTS de legislação e função
  `buscar_legislacao` usada pelo RAG leve (ver `docs/ia.md`).
- `legislacao_batch*.sql` / `legislacao_prioridade_tematica.sql` — ingestão do
  corpus, aplicadas pelo pipeline do painel administrativo (fora deste repo).
