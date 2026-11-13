-- ============================================================================
-- Lint 0029 — Teste do wrapper SECURITY INVOKER do ranking
--
-- O que este script faz:
--   1. Cria, DENTRO DE UMA TRANSAÇÃO, dois usuários fictícios (A e B), um
--      simulado público e um privado de A, e resultados de A e B no público.
--   2. Verifica os metadados: public.ranking_simulado é SECURITY INVOKER,
--      private.ranking_simulado é SECURITY DEFINER, e nenhuma função
--      SECURITY DEFINER de public é executável por anon/authenticated.
--   3. Consulta o ranking como A (criador) e como B (outro aluno), conferindo
--      que o público aparece para os dois e o privado só para o criador.
--   4. Confirma que anon não executa a função (42501).
--   5. Termina com ROLLBACK: nenhum dado de teste fica no banco.
--
-- Como rodar: cole no SQL Editor do Supabase ou execute via MCP
-- (`execute_sql`). Resultado esperado: passou = true e total = 11.
-- ============================================================================

begin;

create temp table _ri_resultados (
    teste text primary key,
    valor bigint not null
) on commit drop;

create temp table _ri_esperado (
    teste text primary key,
    esperado bigint not null
) on commit drop;

grant insert, select on _ri_resultados to anon, authenticated;

-- ---------------------------------------------------------------------------
-- Fixtures (como postgres; revertidas no ROLLBACK)
-- ---------------------------------------------------------------------------
with a as (
    insert into public.usuarios (username, email, auth_id)
    values (
        'ri_a_' || substr(md5(random()::text), 1, 10),
        'ri_a_' || substr(md5(random()::text), 1, 10) || '@example.invalid',
        '77777777-7777-4777-8777-777777777777'
    )
    returning id
)
select set_config('ri.a_id', id::text, true) from a;

with b as (
    insert into public.usuarios (username, email, auth_id)
    values (
        'ri_b_' || substr(md5(random()::text), 1, 10),
        'ri_b_' || substr(md5(random()::text), 1, 10) || '@example.invalid',
        '88888888-8888-4888-8888-888888888888'
    )
    returning id
)
select set_config('ri.b_id', id::text, true) from b;

with s as (
    insert into public.simulados (id_criador, titulo, eh_privado)
    values (current_setting('ri.a_id')::int, 'ri A publico', false)
    returning id
)
select set_config('ri.a_pub', id::text, true) from s;

with s as (
    insert into public.simulados (id_criador, titulo, eh_privado)
    values (current_setting('ri.a_id')::int, 'ri A privado', true)
    returning id
)
select set_config('ri.a_priv', id::text, true) from s;

insert into public.simulados_resultados
    (id_simulado, id_usuario, nota, respostas_corretas, total_questoes)
values
    (current_setting('ri.a_pub')::uuid, current_setting('ri.a_id')::int, 8, 8, 10),
    (current_setting('ri.a_pub')::uuid, current_setting('ri.b_id')::int, 6, 6, 10),
    (current_setting('ri.a_priv')::uuid, current_setting('ri.a_id')::int, 7, 7, 10);

-- ---------------------------------------------------------------------------
-- Metadados e grants
-- ---------------------------------------------------------------------------
insert into _ri_resultados values
    ('public_invoker', case when (
        select not p.prosecdef
        from pg_proc p
        join pg_namespace n on n.oid = p.pronamespace
        where n.nspname = 'public'
          and p.proname = 'ranking_simulado'
          and pg_get_function_identity_arguments(p.oid) = 'p_id_simulado uuid'
    ) then 1 else 0 end),
    ('private_definer', case when (
        select p.prosecdef
        from pg_proc p
        join pg_namespace n on n.oid = p.pronamespace
        where n.nspname = 'private'
          and p.proname = 'ranking_simulado'
          and pg_get_function_identity_arguments(p.oid) = 'p_id_simulado uuid'
    ) then 1 else 0 end),
    ('nenhuma_definer_publica_executavel', (
        select count(*)
        from pg_proc p
        join pg_namespace n on n.oid = p.pronamespace
        where n.nspname = 'public'
          and p.prosecdef
          and (
              has_function_privilege('anon', p.oid, 'execute')
              or has_function_privilege('authenticated', p.oid, 'execute')
          )
    )),
    ('anon_pode_executar_publica', case
        when has_function_privilege('anon', 'public.ranking_simulado(uuid)', 'execute') then 1 else 0
    end),
    ('anon_pode_executar_privada', case
        when has_function_privilege('anon', 'private.ranking_simulado(uuid)', 'execute') then 1 else 0
    end),
    ('authenticated_pode_executar_publica', case
        when has_function_privilege('authenticated', 'public.ranking_simulado(uuid)', 'execute') then 1 else 0
    end);

-- ---------------------------------------------------------------------------
-- ALUNO A (criador): vê o público (2 resultados) e o próprio privado (1)
-- ---------------------------------------------------------------------------
select set_config('request.jwt.claim.sub', '77777777-7777-4777-8777-777777777777', true);
select set_config(
    'request.jwt.claims',
    '{"sub":"77777777-7777-4777-8777-777777777777","role":"authenticated"}',
    true
);
set local role authenticated;

insert into _ri_resultados values
    ('A_ranking_publico', (
        select count(*) from public.ranking_simulado(current_setting('ri.a_pub')::uuid)
    )),
    ('A_ranking_privado_proprio', (
        select count(*) from public.ranking_simulado(current_setting('ri.a_priv')::uuid)
    ));
reset role;

-- ---------------------------------------------------------------------------
-- ALUNO B (não criador): vê o público (2), mas não o privado de A (0)
-- ---------------------------------------------------------------------------
select set_config('request.jwt.claim.sub', '88888888-8888-4888-8888-888888888888', true);
select set_config(
    'request.jwt.claims',
    '{"sub":"88888888-8888-4888-8888-888888888888","role":"authenticated"}',
    true
);
set local role authenticated;

insert into _ri_resultados values
    ('B_ranking_publico', (
        select count(*) from public.ranking_simulado(current_setting('ri.a_pub')::uuid)
    )),
    ('B_ranking_privado_alheio', (
        select count(*) from public.ranking_simulado(current_setting('ri.a_priv')::uuid)
    ));
reset role;

-- ---------------------------------------------------------------------------
-- ANON: sem EXECUTE no wrapper público (42501)
-- ---------------------------------------------------------------------------
select set_config('request.jwt.claim.sub', '', true);
select set_config('request.jwt.claims', '{"role":"anon"}', true);
set local role anon;

do $$
declare
    v_erro text;
begin
    begin
        perform * from public.ranking_simulado('00000000-0000-4000-8000-000000000000');
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _ri_resultados values ('anon_chamada_falha_42501', case when v_erro = '42501' then 1 else 0 end);
end $$;
reset role;

-- ---------------------------------------------------------------------------
-- Expectativas
-- ---------------------------------------------------------------------------
insert into _ri_esperado values
    ('public_invoker', 1),
    ('private_definer', 1),
    ('nenhuma_definer_publica_executavel', 0),
    ('anon_pode_executar_publica', 0),
    ('anon_pode_executar_privada', 0),
    ('authenticated_pode_executar_publica', 1),
    ('A_ranking_publico', 2),
    ('A_ranking_privado_proprio', 1),
    ('B_ranking_publico', 2),
    ('B_ranking_privado_alheio', 0),
    ('anon_chamada_falha_42501', 1);

select
    bool_and(r.valor = e.esperado) as passou,
    count(*) as total,
    count(*) filter (where r.valor <> e.esperado) as falhas,
    jsonb_agg(
        jsonb_build_object(
            'teste', e.teste,
            'esperado', e.esperado,
            'obtido', r.valor,
            'ok', r.valor = e.esperado
        )
        order by e.teste
    ) as resultados
from _ri_esperado e
join _ri_resultados r using (teste);

rollback;
