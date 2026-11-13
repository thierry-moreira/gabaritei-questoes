-- ============================================================================
-- Lint 0006 — Teste da policy consolidada de UPDATE em usuarios
--
-- O que este script faz:
--   1. Cria, DENTRO DE UMA TRANSAÇÃO, dois perfis legados (auth_id NULL,
--      e-mails diferentes) e um aluno B com auth_id.
--   2. Como aluno A (JWT com o e-mail de um dos legados + x-app-token),
--      confere que o UPDATE adota SOMENTE a linha legada de mesmo e-mail,
--      não toca na linha de B e não troca o auth_id para terceiros.
--   3. Confere que a atualização do próprio perfil continua permitida e que
--      sem x-app-token ou como anon o UPDATE é bloqueado.
--   4. Verifica que existe apenas UMA policy permissiva de UPDATE para
--      `authenticated` (lint 0006 zerado).
--   5. Termina com ROLLBACK: nenhum dado de teste fica no banco.
--
-- Como rodar: cole no SQL Editor do Supabase ou execute via MCP
-- (`execute_sql`). Resultado esperado: passou = true e total = 10.
-- ============================================================================

begin;

create temp table _upd_resultados (
    teste text primary key,
    valor bigint not null
) on commit drop;

create temp table _upd_esperado (
    teste text primary key,
    esperado bigint not null
) on commit drop;

grant insert, select on _upd_resultados to anon, authenticated;

-- ---------------------------------------------------------------------------
-- Fixtures (como postgres; revertidas no ROLLBACK)
-- ---------------------------------------------------------------------------
select set_config('upd.a_auth', '99999999-9999-4999-8999-999999999999', true);
select set_config(
    'upd.l_email',
    'legacy_' || substr(md5(random()::text), 1, 10) || '@example.invalid',
    true
);
select set_config(
    'upd.l2_email',
    'legacy2_' || substr(md5(random()::text), 1, 10) || '@example.invalid',
    true
);

with l as (
    insert into public.usuarios (username, email, auth_id)
    values (
        'upd_l_' || substr(md5(random()::text), 1, 8),
        current_setting('upd.l_email'),
        null
    )
    returning id
)
select set_config('upd.l_id', id::text, true) from l;

with l2 as (
    insert into public.usuarios (username, email, auth_id)
    values (
        'upd_l2_' || substr(md5(random()::text), 1, 8),
        current_setting('upd.l2_email'),
        null
    )
    returning id
)
select set_config('upd.l2_id', id::text, true) from l2;

with b as (
    insert into public.usuarios (username, email, auth_id)
    values (
        'upd_b_' || substr(md5(random()::text), 1, 8),
        'upd_b_' || substr(md5(random()::text), 1, 8) || '@example.invalid',
        'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
    )
    returning id
)
select set_config('upd.b_id', id::text, true) from b;

-- ---------------------------------------------------------------------------
-- Metadados: uma única policy permissiva de UPDATE para authenticated
-- ---------------------------------------------------------------------------
insert into _upd_resultados values
    ('uma_policy_update_authenticated', (
        select count(*)
        from pg_policies
        where schemaname = 'public'
          and tablename = 'usuarios'
          and cmd = 'UPDATE'
          and 'authenticated' = any(roles)
    )),
    ('policy_consolidada_existe', case when exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'usuarios'
          and policyname = 'usuarios_update_proprio_ou_relink'
          and cmd = 'UPDATE'
    ) then 1 else 0 end);

-- ---------------------------------------------------------------------------
-- ALUNO A: JWT do e-mail legado (em MAIÚSCULAS para testar lower()) + token
-- ---------------------------------------------------------------------------
select set_config('request.jwt.claim.sub', current_setting('upd.a_auth'), true);
select set_config(
    'request.jwt.claims',
    json_build_object(
        'sub', current_setting('upd.a_auth'),
        'role', 'authenticated',
        'email', upper(current_setting('upd.l_email'))
    )::text,
    true
);
select set_config(
    'request.headers',
    json_build_object(
        'x-app-token',
        (regexp_match(
            pg_get_functiondef('public.eh_app_aluno()'::regprocedure),
            '''([0-9a-f]{64})'''
        ))[1]
    )::text,
    true
);

set local role authenticated;

-- O app filtra apenas auth_id IS NULL; o RLS restringe ao e-mail do JWT.
do $$
declare
    v_linhas int;
begin
    update public.usuarios
    set auth_id = current_setting('upd.a_auth')::uuid
    where auth_id is null;
    get diagnostics v_linhas = row_count;
    insert into _upd_resultados values ('A_relink_afeta_so_email_correspondente', v_linhas);
end $$;

do $$
declare
    v_linhas int;
begin
    update public.usuarios
    set tema = 'claro'
    where id = current_setting('upd.l_id')::int;
    get diagnostics v_linhas = row_count;
    insert into _upd_resultados values ('A_atualiza_perfil_proprio', v_linhas);
end $$;

do $$
declare
    v_linhas int;
begin
    update public.usuarios
    set tema = 'x'
    where id = current_setting('upd.b_id')::int;
    get diagnostics v_linhas = row_count;
    insert into _upd_resultados values ('A_nao_atualiza_B', v_linhas);
end $$;

do $$
declare
    v_erro text;
begin
    begin
        update public.usuarios
        set auth_id = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'::uuid
        where id = current_setting('upd.l_id')::int;
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _upd_resultados values (
        'A_nao_troca_auth_id_para_terceiro',
        case when v_erro = '42501' then 1 else 0 end
    );
end $$;

-- Sem o header x-app-token, eh_app_aluno() bloqueia o UPDATE.
select set_config('request.headers', '{}', true);

do $$
declare
    v_linhas int;
begin
    update public.usuarios
    set tema = 'x'
    where id = current_setting('upd.l_id')::int;
    get diagnostics v_linhas = row_count;
    insert into _upd_resultados values (
        'sem_app_token_bloqueia',
        case when v_linhas = 0 then 1 else 0 end
    );
end $$;

reset role;

-- ---------------------------------------------------------------------------
-- ANON: sem JWT e sem grant de UPDATE (bloqueado por grant ou por RLS)
-- ---------------------------------------------------------------------------
select set_config('request.jwt.claim.sub', '', true);
select set_config('request.jwt.claims', '{"role":"anon"}', true);
set local role anon;

do $$
declare
    v_erro text;
    v_linhas int := 0;
begin
    begin
        update public.usuarios
        set tema = 'x'
        where id = current_setting('upd.l2_id')::int;
        get diagnostics v_linhas = row_count;
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _upd_resultados values (
        'anon_bloqueado',
        case when v_erro is not null or v_linhas = 0 then 1 else 0 end
    );
end $$;

reset role;

-- ---------------------------------------------------------------------------
-- Estado final (como postgres): só a linha de mesmo e-mail foi adotada
-- ---------------------------------------------------------------------------
insert into _upd_resultados values
    ('L_vinculado_a_A', (
        select count(*) from public.usuarios
        where id = current_setting('upd.l_id')::int
          and auth_id = current_setting('upd.a_auth')::uuid
    )),
    ('L2_permanece_sem_vinculo', (
        select count(*) from public.usuarios
        where id = current_setting('upd.l2_id')::int
          and auth_id is null
    ));

-- ---------------------------------------------------------------------------
-- Expectativas
-- ---------------------------------------------------------------------------
insert into _upd_esperado values
    ('uma_policy_update_authenticated', 1),
    ('policy_consolidada_existe', 1),
    ('A_relink_afeta_so_email_correspondente', 1),
    ('A_atualiza_perfil_proprio', 1),
    ('A_nao_atualiza_B', 0),
    ('A_nao_troca_auth_id_para_terceiro', 1),
    ('sem_app_token_bloqueia', 1),
    ('anon_bloqueado', 1),
    ('L_vinculado_a_A', 1),
    ('L2_permanece_sem_vinculo', 1);

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
from _upd_esperado e
join _upd_resultados r using (teste);

rollback;
