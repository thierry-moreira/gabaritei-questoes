-- ============================================================================
-- F-04 — Teste transacional: resultado de simulado só em simulado público ou
-- do próprio aluno.
--
-- Cria dois alunos (A e B) e dois simulados para cada (um público e um
-- privado), dentro de uma transação revertida no final. Verifica, como
-- `authenticated` (JWT + x-app-token):
--   * A grava resultado no próprio simulado privado;
--   * B grava resultado no próprio simulado privado;
--   * B NÃO grava resultado no simulado privado de A (42501);
--   * B grava resultado no simulado público de A;
--   * B NÃO grava resultado spoofando o id_usuario de A (42501);
--   * B atualiza o próprio resultado em simulado público;
--   * B NÃO move o próprio resultado para o simulado privado de A (42501);
--   * B NÃO atualiza o resultado de A (0 linhas);
--   * o ranking público de A aparece para B; o privado de A não;
--   * o ranking privado de A só aparece para A.
--
-- Não depende de questões: simulados_resultados e ranking_simulado só usam
-- simulados/usuarios.
--
-- Resultado esperado: passou = true, total = 13, falhas = 0.
-- Termina com ROLLBACK: nenhum dado de teste fica no banco.
-- ============================================================================

begin;

create temp table _f04_resultados (
    teste text primary key,
    esperado text not null,
    obtido text not null,
    passou boolean not null
) on commit drop;

-- ---------------------------------------------------------------------------
-- Fixtures (como postgres; revertidas no ROLLBACK)
-- ---------------------------------------------------------------------------
with a as (
    insert into public.usuarios (username, email, auth_id)
    values (
        'f04_a_' || substr(md5(random()::text), 1, 10),
        'f04_a_' || substr(md5(random()::text), 1, 10) || '@example.invalid',
        '11111111-1111-4111-8111-111111111111'
    )
    returning id
)
select set_config('f04.a_id', id::text, true) from a;

with b as (
    insert into public.usuarios (username, email, auth_id)
    values (
        'f04_b_' || substr(md5(random()::text), 1, 10),
        'f04_b_' || substr(md5(random()::text), 1, 10) || '@example.invalid',
        '22222222-2222-4222-8222-222222222222'
    )
    returning id
)
select set_config('f04.b_id', id::text, true) from b;

with s as (
    insert into public.simulados (id_criador, titulo, eh_privado)
    values (current_setting('f04.a_id')::int, 'f04 A publico', false)
    returning id
)
select set_config('f04.a_pub', id::text, true) from s;

with s as (
    insert into public.simulados (id_criador, titulo, eh_privado)
    values (current_setting('f04.a_id')::int, 'f04 A privado', true)
    returning id
)
select set_config('f04.a_priv', id::text, true) from s;

with s as (
    insert into public.simulados (id_criador, titulo, eh_privado)
    values (current_setting('f04.b_id')::int, 'f04 B privado', true)
    returning id
)
select set_config('f04.b_priv', id::text, true) from s;

do $$
declare
    v_a_id int := current_setting('f04.a_id')::int;
    v_b_id int := current_setting('f04.b_id')::int;
    v_a_auth text := '11111111-1111-4111-8111-111111111111';
    v_b_auth text := '22222222-2222-4222-8222-222222222222';
    v_a_pub uuid := current_setting('f04.a_pub')::uuid;
    v_a_priv uuid := current_setting('f04.a_priv')::uuid;
    v_b_priv uuid := current_setting('f04.b_priv')::uuid;
    v_token text;
    v_erro text;
    v_linhas int;
    v_qtd bigint;
begin
    -- O token de app vive dentro de public.eh_app_aluno(); é lido em runtime
    -- para o teste não gravar o segredo no repositório.
    select (regexp_match(
        pg_get_functiondef('public.eh_app_aluno()'::regprocedure),
        '''([0-9a-f]{64})'''
    ))[1] into v_token;

    if v_token is null then
        raise exception 'test_f04: não foi possível ler o token de eh_app_aluno()';
    end if;

    perform set_config(
        'request.headers',
        json_build_object('x-app-token', v_token)::text,
        true
    );

    -- -----------------------------------------------------------------------
    -- A: INSERT no próprio simulado privado (permitido)
    -- -----------------------------------------------------------------------
    perform set_config('request.jwt.claim.sub', v_a_auth, true);
    perform set_config(
        'request.jwt.claims',
        json_build_object('sub', v_a_auth, 'role', 'authenticated')::text,
        true
    );
    execute 'set local role authenticated';
    v_erro := null;
    begin
        insert into public.simulados_resultados
            (id_simulado, id_usuario, nota, respostas_corretas, total_questoes)
        values (v_a_priv, v_a_id, 9, 9, 10);
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f04_resultados values (
        'A_insere_no_proprio_privado', 'OK',
        coalesce(v_erro, 'OK'), coalesce(v_erro, 'OK') = 'OK'
    );

    -- -----------------------------------------------------------------------
    -- B: INSERT no próprio simulado privado (permitido)
    -- -----------------------------------------------------------------------
    perform set_config('request.jwt.claim.sub', v_b_auth, true);
    perform set_config(
        'request.jwt.claims',
        json_build_object('sub', v_b_auth, 'role', 'authenticated')::text,
        true
    );
    execute 'set local role authenticated';
    v_erro := null;
    begin
        insert into public.simulados_resultados
            (id_simulado, id_usuario, nota, respostas_corretas, total_questoes)
        values (v_b_priv, v_b_id, 7, 7, 10);
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f04_resultados values (
        'B_insere_no_proprio_privado', 'OK',
        coalesce(v_erro, 'OK'), coalesce(v_erro, 'OK') = 'OK'
    );

    -- -----------------------------------------------------------------------
    -- B: INSERT no simulado privado de A (bloqueado pela policy)
    -- -----------------------------------------------------------------------
    execute 'set local role authenticated';
    v_erro := null;
    begin
        insert into public.simulados_resultados
            (id_simulado, id_usuario, nota, respostas_corretas, total_questoes)
        values (v_a_priv, v_b_id, 10, 10, 10);
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f04_resultados values (
        'B_insere_no_privado_de_A', '42501',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '42501'
    );

    -- -----------------------------------------------------------------------
    -- B: INSERT no simulado público de A (permitido; é público por desenho)
    -- -----------------------------------------------------------------------
    execute 'set local role authenticated';
    v_erro := null;
    begin
        insert into public.simulados_resultados
            (id_simulado, id_usuario, nota, respostas_corretas, total_questoes)
        values (v_a_pub, v_b_id, 6, 6, 10);
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f04_resultados values (
        'B_insere_no_publico_de_A', 'OK',
        coalesce(v_erro, 'OK'), coalesce(v_erro, 'OK') = 'OK'
    );

    -- -----------------------------------------------------------------------
    -- B: INSERT spoofando o id_usuario de A (bloqueado por eh_dono_do_aluno)
    -- -----------------------------------------------------------------------
    execute 'set local role authenticated';
    v_erro := null;
    begin
        insert into public.simulados_resultados
            (id_simulado, id_usuario, nota, respostas_corretas, total_questoes)
        values (v_a_pub, v_a_id, 10, 10, 10);
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f04_resultados values (
        'B_insere_com_dono_spoofado', '42501',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '42501'
    );

    -- -----------------------------------------------------------------------
    -- B: UPDATE do próprio resultado em simulado público (permitido)
    -- -----------------------------------------------------------------------
    execute 'set local role authenticated';
    v_erro := null;
    v_linhas := null;
    begin
        update public.simulados_resultados
           set nota = 8
         where id_simulado = v_a_pub
           and id_usuario = v_b_id;
        get diagnostics v_linhas = row_count;
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f04_resultados values (
        'B_atualiza_publico_de_A', '1',
        coalesce(v_erro, v_linhas::text),
        v_erro is null and v_linhas = 1
    );

    -- -----------------------------------------------------------------------
    -- B: mover o próprio resultado para o privado de A (bloqueado no CHECK)
    -- -----------------------------------------------------------------------
    execute 'set local role authenticated';
    v_erro := null;
    begin
        update public.simulados_resultados
           set id_simulado = v_a_priv
         where id_simulado = v_a_pub
           and id_usuario = v_b_id;
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f04_resultados values (
        'B_move_resultado_para_privado_de_A', '42501',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '42501'
    );

    -- -----------------------------------------------------------------------
    -- B: UPDATE no resultado de A (0 linhas: USING não enxerga a linha)
    -- -----------------------------------------------------------------------
    execute 'set local role authenticated';
    v_erro := null;
    v_linhas := null;
    begin
        update public.simulados_resultados
           set nota = 0
         where id_simulado = v_a_priv
           and id_usuario = v_a_id;
        get diagnostics v_linhas = row_count;
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f04_resultados values (
        'B_atualiza_resultado_de_A', '0',
        coalesce(v_erro, v_linhas::text),
        v_erro is null and v_linhas = 0
    );

    -- -----------------------------------------------------------------------
    -- Ranking: B não vê o privado de A, mas vê o público de A
    -- -----------------------------------------------------------------------
    execute 'set local role authenticated';
    v_erro := null;
    v_qtd := null;
    begin
        select count(*) into v_qtd
        from public.ranking_simulado(v_a_priv);
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f04_resultados values (
        'B_ranking_privado_de_A', '0',
        coalesce(v_erro, v_qtd::text),
        v_erro is null and v_qtd = 0
    );

    execute 'set local role authenticated';
    v_erro := null;
    v_qtd := null;
    begin
        select count(*) into v_qtd
        from public.ranking_simulado(v_a_pub);
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f04_resultados values (
        'B_ranking_publico_de_A', '1',
        coalesce(v_erro, v_qtd::text),
        v_erro is null and v_qtd = 1
    );

    -- -----------------------------------------------------------------------
    -- Ranking: A vê o próprio privado; não vê o privado de B
    -- -----------------------------------------------------------------------
    perform set_config('request.jwt.claim.sub', v_a_auth, true);
    perform set_config(
        'request.jwt.claims',
        json_build_object('sub', v_a_auth, 'role', 'authenticated')::text,
        true
    );

    -- -----------------------------------------------------------------------
    -- A: INSERT no simulado privado de B (bloqueado pela policy)
    -- -----------------------------------------------------------------------
    execute 'set local role authenticated';
    v_erro := null;
    begin
        insert into public.simulados_resultados
            (id_simulado, id_usuario, nota, respostas_corretas, total_questoes)
        values (v_b_priv, v_a_id, 10, 10, 10);
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f04_resultados values (
        'A_insere_no_privado_de_B', '42501',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '42501'
    );

    execute 'set local role authenticated';
    v_erro := null;
    v_qtd := null;
    begin
        select count(*) into v_qtd
        from public.ranking_simulado(v_a_priv);
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f04_resultados values (
        'A_ranking_privado_proprio', '1',
        coalesce(v_erro, v_qtd::text),
        v_erro is null and v_qtd = 1
    );

    execute 'set local role authenticated';
    v_erro := null;
    v_qtd := null;
    begin
        select count(*) into v_qtd
        from public.ranking_simulado(v_b_priv);
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f04_resultados values (
        'A_ranking_privado_de_B', '0',
        coalesce(v_erro, v_qtd::text),
        v_erro is null and v_qtd = 0
    );
end $$;

-- ---------------------------------------------------------------------------
-- Resultado
-- ---------------------------------------------------------------------------
select
    bool_and(passou) as passou,
    count(*)::int as total,
    count(*) filter (where not passou)::int as falhas,
    jsonb_agg(
        jsonb_build_object(
            'teste', teste,
            'esperado', esperado,
            'obtido', obtido,
            'passou', passou
        )
        order by teste
    ) as resultados
from _f04_resultados;

rollback;
