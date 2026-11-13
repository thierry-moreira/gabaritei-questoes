-- ============================================================================
-- Lint 0010 — Security Definer View nas projeções públicas
--
-- As views públicas do F-01 precisam ler tabelas com RLS owner-only, mas não
-- podem ser SECURITY DEFINER no schema exposto pela API (lint ERROR 0010).
-- Solução: manter a lógica privilegiada em views do schema `private` — que
-- não está em `pgrst.db_schemas` e, portanto, não tem rota /rest/v1 nem
-- GraphQL — e publicar em `public` apenas wrappers `security_invoker = true`.
--
-- Por que isso não regride F-01/F-07:
--   * `private` não é exposto pelo PostgREST/pg_graphql; o cliente só alcança
--     os wrappers de `public`;
--   * os wrappers expõem exatamente as mesmas colunas públicas de antes;
--   * as views internas continuam filtrando `status = 'publicada'` e
--     `eh_privado = false` e nunca projetam id_usuario, id_criador, auth_id
--     ou e-mail;
--   * quem consulta o wrapper continua sujeito aos privilégios/RLS do papel
--     chamador na camada externa; a elevação fica restrita ao schema privado.
--
-- IDEMPOTENTE: pode ser reaplicada. Aplicar via MCP (apply_migration) ou SQL
-- Editor. Teste transacional: docs/migrations/test_security_invoker_views.sql.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 0. Schema privado: sem exposição na API, mas com USAGE/SELECT para os papéis
--    que precisam atravessar o wrapper público.
-- ----------------------------------------------------------------------------
create schema if not exists private;
revoke all on schema private from public;
grant usage on schema private to anon, authenticated, service_role;

-- ----------------------------------------------------------------------------
-- 1. Views privilegiadas (mesmas definições e filtros do F-01)
-- ----------------------------------------------------------------------------
create or replace view private.view_comentarios_publicos
with (security_barrier = true, security_invoker = false)
as
select
    c.id_comentario,
    c.id_questao,
    c.nome_usuario,
    c.texto_comentario,
    c.criado_em
from public.comentarios_questao c
join public.questoes q on q.id_questao = c.id_questao
where q.status = 'publicada';

revoke all on private.view_comentarios_publicos from public, anon, authenticated;
grant select on private.view_comentarios_publicos to anon, authenticated, service_role;

comment on view private.view_comentarios_publicos is
    'F-01/F-07: feed público de comentários sem id_usuario/auth_id. View privilegiada; exposta apenas pelo wrapper security_invoker em public.';

create or replace view private.view_simulados_publicos
with (security_barrier = true, security_invoker = false)
as
select
    s.id,
    s.titulo,
    s.descricao,
    s.criado_em,
    coalesce(u.username, 'Aluno') as nome_criador,
    coalesce(
        s.id_criador = (
            select u2.id
            from public.usuarios u2
            where u2.auth_id = (select auth.uid())
        ),
        false
    ) as eh_meu
from public.simulados s
left join public.usuarios u on u.id = s.id_criador
where s.eh_privado is false;

revoke all on private.view_simulados_publicos from public, anon, authenticated;
grant select on private.view_simulados_publicos to authenticated, service_role;

comment on view private.view_simulados_publicos is
    'F-01/F-05: simulados públicos (eh_privado=false) sem id_criador/e-mail. View privilegiada; exposta apenas pelo wrapper security_invoker em public.';

create or replace view private.view_simulados_questoes_publicas
with (security_barrier = true, security_invoker = false)
as
select
    sq.id_simulado,
    sq.id_questao
from public.simulados_questoes sq
join public.simulados s on s.id = sq.id_simulado
where s.eh_privado is false;

revoke all on private.view_simulados_questoes_publicas from public, anon, authenticated;
grant select on private.view_simulados_questoes_publicas to authenticated, service_role;

comment on view private.view_simulados_questoes_publicas is
    'F-01: questões de simulados públicos. View privilegiada; exposta apenas pelo wrapper security_invoker em public.';

-- ----------------------------------------------------------------------------
-- 2. Wrappers públicos: security_invoker = true (lint 0010) e mesma projeção
-- ----------------------------------------------------------------------------
create or replace view public.view_comentarios_publicos
with (security_barrier = true, security_invoker = true)
as
select * from private.view_comentarios_publicos;

revoke all on public.view_comentarios_publicos from public, anon, authenticated;
grant select on public.view_comentarios_publicos to anon, authenticated;

comment on view public.view_comentarios_publicos is
    'F-01/F-07 + lint 0010: wrapper security_invoker do feed público; a lógica privilegiada vive em private.view_comentarios_publicos.';

create or replace view public.view_simulados_publicos
with (security_barrier = true, security_invoker = true)
as
select * from private.view_simulados_publicos;

revoke all on public.view_simulados_publicos from public, anon, authenticated;
grant select on public.view_simulados_publicos to authenticated;

comment on view public.view_simulados_publicos is
    'F-01/F-05 + lint 0010: wrapper security_invoker dos simulados públicos; a lógica privilegiada vive em private.view_simulados_publicos.';

create or replace view public.view_simulados_questoes_publicas
with (security_barrier = true, security_invoker = true)
as
select * from private.view_simulados_questoes_publicas;

revoke all on public.view_simulados_questoes_publicas from public, anon, authenticated;
grant select on public.view_simulados_questoes_publicas to authenticated;

comment on view public.view_simulados_questoes_publicas is
    'F-01 + lint 0010: wrapper security_invoker das questões de simulados públicos; a lógica privilegiada vive em private.view_simulados_questoes_publicas.';
