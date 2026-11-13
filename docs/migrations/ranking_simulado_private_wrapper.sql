-- ============================================================================
-- Lint 0029 — Security Definer Function no ranking
--
-- O ranking precisa ler simulados_resultados de outros alunos, mas a tabela
-- tem RLS owner-only. A função SECURITY DEFINER original ficava em public, o
-- que dispara o lint 0029 para qualquer usuário autenticado. Solução: mover a
-- lógica privilegiada para private.ranking_simulado e manter em public apenas
-- um wrapper SECURITY INVOKER com a mesma assinatura.
--
-- Por que isso não regride F-05:
--   * private não é exposto pelo PostgREST (fora de pgrst.db_schemas);
--   * a função interna continua checando auth.uid(), liberando ranking de
--     simulado público para qualquer autenticado e o privado apenas ao criador;
--   * a projeção continua sendo username + métricas, nunca id_usuario;
--   * o app segue chamando rpc('ranking_simulado'), sem mudança de código.
--
-- IDEMPOTENTE: pode ser reaplicada. Aplicar via MCP (apply_migration) ou SQL
-- Editor. Teste transacional: docs/migrations/test_ranking_invoker.sql.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Função privilegiada no schema privado (não exposto pela API)
-- ----------------------------------------------------------------------------
create or replace function private.ranking_simulado(p_id_simulado uuid)
returns table (
    nome_usuario text,
    nota double precision,
    respostas_corretas integer,
    total_questoes integer,
    data_conclusao timestamptz
)
language sql
stable
security definer
set search_path = ''
as $function$
    select
        u.username,
        r.nota,
        r.respostas_corretas,
        r.total_questoes,
        r.data_conclusao
    from public.simulados_resultados r
    join public.simulados s on s.id = r.id_simulado
    join public.usuarios u on u.id = r.id_usuario
    where r.id_simulado = p_id_simulado
      and (select auth.uid()) is not null
      and (
          s.eh_privado is false
          or s.id_criador = (
              select u2.id
              from public.usuarios u2
              where u2.auth_id = (select auth.uid())
          )
      )
    order by r.nota desc, r.data_conclusao asc
    limit 50;
$function$;

revoke all on function private.ranking_simulado(uuid) from public, anon;
grant execute on function private.ranking_simulado(uuid) to authenticated, service_role;

comment on function private.ranking_simulado(uuid) is
    'F-05: lógica privilegiada do ranking; exposta apenas pelo wrapper security invoker em public.';

-- ----------------------------------------------------------------------------
-- 2. Wrapper público SECURITY INVOKER (lint 0029) com a mesma assinatura
-- ----------------------------------------------------------------------------
create or replace function public.ranking_simulado(p_id_simulado uuid)
returns table (
    nome_usuario text,
    nota double precision,
    respostas_corretas integer,
    total_questoes integer,
    data_conclusao timestamptz
)
language sql
stable
security invoker
set search_path = ''
as $function$
    select *
    from private.ranking_simulado(p_id_simulado);
$function$;

revoke all on function public.ranking_simulado(uuid) from public, anon;
grant execute on function public.ranking_simulado(uuid) to authenticated;

comment on function public.ranking_simulado(uuid) is
    'F-05 + lint 0029: wrapper security invoker; a lógica SECURITY DEFINER vive em private.ranking_simulado.';
