-- ============================================================================
-- F-03 — Teste transacional: vínculo de questão só no próprio caderno
--
-- Cria dois alunos (A e B) e um caderno para cada, dentro de uma transação
-- revertida no final. Verifica, como `authenticated` (JWT + x-app-token):
--   * A e B inserem nos próprios cadernos;
--   * B NÃO insere no caderno de A (nem com id_usuario=B, nem com o
--     id_usuario de A spoofado);
--   * B NÃO move o próprio vínculo para o caderno de A.
-- Verifica, como postgres (para isolar a constraint da RLS):
--   * INSERT/UPDATE cross-tenant é barrado pela FK composta (23503);
--   * id_usuario NULL é barrado (23502);
--   * ON DELETE CASCADE do caderno remove os vínculos.
--
-- Pré-requisito: existir pelo menos duas questões com status = 'publicada'
-- (a segunda isola a FK da PK composta nos casos de INSERT/UPDATE).
-- Resultado esperado: passou = true, total = 12, falhas = 0.
-- Termina com ROLLBACK: nenhum dado de teste fica no banco.
-- ============================================================================

begin;

create temp table _f03_resultados (
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
        'f03_a_' || substr(md5(random()::text), 1, 10),
        'f03_a_' || substr(md5(random()::text), 1, 10) || '@example.invalid',
        '55555555-5555-4555-8555-555555555555'
    )
    returning id
)
select set_config('f03.a_id', id::text, true) from a;

with b as (
    insert into public.usuarios (username, email, auth_id)
    values (
        'f03_b_' || substr(md5(random()::text), 1, 10),
        'f03_b_' || substr(md5(random()::text), 1, 10) || '@example.invalid',
        '66666666-6666-4666-8666-666666666666'
    )
    returning id
)
select set_config('f03.b_id', id::text, true) from b;

select set_config('f03.a_auth', '55555555-5555-4555-8555-555555555555', true);
select set_config('f03.b_auth', '66666666-6666-4666-8666-666666666666', true);

select set_config('f03.q_id', id_questao::text, true)
from public.questoes
where status = 'publicada'
order by id_questao
limit 1;

select set_config('f03.q2_id', id_questao::text, true)
from public.questoes
where status = 'publicada'
order by id_questao
offset 1
limit 1;

do $$
begin
    if current_setting('f03.q_id', true) is null
       or current_setting('f03.q2_id', true) is null then
        raise exception 'test_f03: são necessárias duas questões com status = publicada';
    end if;
end $$;

with c as (
    insert into public.cadernos (id_usuario, nome_caderno)
    values (current_setting('f03.a_id')::int, 'f03 caderno A')
    returning id_caderno
)
select set_config('f03.a_caderno', id_caderno::text, true) from c;

with c as (
    insert into public.cadernos (id_usuario, nome_caderno)
    values (current_setting('f03.b_id')::int, 'f03 caderno B')
    returning id_caderno
)
select set_config('f03.b_caderno', id_caderno::text, true) from c;

-- ---------------------------------------------------------------------------
-- 1. Como alunos autenticados (RLS + policies)
-- ---------------------------------------------------------------------------
do $$
declare
    v_a_id int := current_setting('f03.a_id')::int;
    v_b_id int := current_setting('f03.b_id')::int;
    v_a_auth text := current_setting('f03.a_auth');
    v_b_auth text := current_setting('f03.b_auth');
    v_a_cad uuid := current_setting('f03.a_caderno')::uuid;
    v_b_cad uuid := current_setting('f03.b_caderno')::uuid;
    v_q int := current_setting('f03.q_id')::int;
    v_token text;
    v_erro text;
begin
    -- O token de app vive dentro de public.eh_app_aluno(); é lido em runtime
    -- para o teste não gravar o segredo no repositório.
    select (regexp_match(
        pg_get_functiondef('public.eh_app_aluno()'::regprocedure),
        '''([0-9a-f]{64})'''
    ))[1] into v_token;

    if v_token is null then
        raise exception 'test_f03: não foi possível ler o token de eh_app_aluno()';
    end if;

    perform set_config(
        'request.headers',
        json_build_object('x-app-token', v_token)::text,
        true
    );

    -- A insere no próprio caderno.
    perform set_config('request.jwt.claim.sub', v_a_auth, true);
    perform set_config(
        'request.jwt.claims',
        json_build_object('sub', v_a_auth, 'role', 'authenticated')::text,
        true
    );
    execute 'set local role authenticated';
    v_erro := null;
    begin
        insert into public.caderno_questoes (id_caderno, id_questao, id_usuario)
        values (v_a_cad, v_q, v_a_id);
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f03_resultados values (
        'A_insere_no_proprio_caderno', 'OK',
        coalesce(v_erro, 'OK'), coalesce(v_erro, 'OK') = 'OK'
    );

    -- B insere no próprio caderno.
    perform set_config('request.jwt.claim.sub', v_b_auth, true);
    perform set_config(
        'request.jwt.claims',
        json_build_object('sub', v_b_auth, 'role', 'authenticated')::text,
        true
    );
    execute 'set local role authenticated';
    v_erro := null;
    begin
        insert into public.caderno_questoes (id_caderno, id_questao, id_usuario)
        values (v_b_cad, v_q, v_b_id);
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f03_resultados values (
        'B_insere_no_proprio_caderno', 'OK',
        coalesce(v_erro, 'OK'), coalesce(v_erro, 'OK') = 'OK'
    );

    -- B tenta inserir no caderno de A com o próprio id_usuario.
    execute 'set local role authenticated';
    v_erro := null;
    begin
        insert into public.caderno_questoes (id_caderno, id_questao, id_usuario)
        values (v_a_cad, v_q, v_b_id);
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f03_resultados values (
        'B_insere_no_caderno_de_A', '42501/23503',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') in ('42501', '23503')
    );

    -- B tenta inserir no caderno de A spoofando o id_usuario de A.
    -- A FK composta aceitaria o par (caderno A, usuário A); quem barra é a
    -- policy, que exige que o caderno pertença ao usuário autenticado.
    execute 'set local role authenticated';
    v_erro := null;
    begin
        insert into public.caderno_questoes (id_caderno, id_questao, id_usuario)
        values (v_a_cad, v_q, v_a_id);
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f03_resultados values (
        'B_insere_com_dono_spoofado', '42501',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '42501'
    );

    -- B tenta mover o próprio vínculo para o caderno de A.
    execute 'set local role authenticated';
    v_erro := null;
    begin
        update public.caderno_questoes
           set id_caderno = v_a_cad
         where id_caderno = v_b_cad
           and id_questao = v_q
           and id_usuario = v_b_id;
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f03_resultados values (
        'B_move_vinculo_para_caderno_de_A', '42501/23503',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') in ('42501', '23503')
    );

    -- B tenta trocar o dono do próprio vínculo para A.
    execute 'set local role authenticated';
    v_erro := null;
    begin
        update public.caderno_questoes
           set id_usuario = v_a_id
         where id_caderno = v_b_cad
           and id_questao = v_q
           and id_usuario = v_b_id;
    exception when others then
        v_erro := sqlstate;
    end;
    execute 'reset role';
    insert into _f03_resultados values (
        'B_troca_dono_do_vinculo', '42501/23503',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') in ('42501', '23503')
    );
end $$;

-- ---------------------------------------------------------------------------
-- 2. Como postgres (sem RLS): a constraint sozinha barra cross-tenant
-- ---------------------------------------------------------------------------
do $$
declare
    v_a_id int := current_setting('f03.a_id')::int;
    v_b_id int := current_setting('f03.b_id')::int;
    v_a_cad uuid := current_setting('f03.a_caderno')::uuid;
    v_b_cad uuid := current_setting('f03.b_caderno')::uuid;
    v_q int := current_setting('f03.q_id')::int;
    v_q2 int := current_setting('f03.q2_id')::int;
    v_erro text;
begin
    -- B (id_usuario) no caderno de A: FK composta -> 23503.
    -- Usa a questão 2, que não existe no caderno de A, para não esbarrar
    -- antes na PK composta (id_caderno, id_questao).
    v_erro := null;
    begin
        insert into public.caderno_questoes (id_caderno, id_questao, id_usuario)
        values (v_a_cad, v_q2, v_b_id);
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _f03_resultados values (
        'FK_bloqueia_cross_tenant_no_insert', '23503',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '23503'
    );

    -- id_usuario NULL: NOT NULL -> 23502.
    v_erro := null;
    begin
        insert into public.caderno_questoes (id_caderno, id_questao, id_usuario)
        values (v_b_cad, v_q2, null);
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _f03_resultados values (
        'id_usuario_null_bloqueado', '23502',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '23502'
    );

    -- Mover vínculo de B para o caderno de A: FK composta -> 23503.
    -- Troca também a questão para a 2, evitando a PK composta.
    v_erro := null;
    begin
        update public.caderno_questoes
           set id_caderno = v_a_cad,
               id_questao = v_q2
         where id_caderno = v_b_cad
           and id_questao = v_q
           and id_usuario = v_b_id;
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _f03_resultados values (
        'FK_bloqueia_cross_tenant_no_update', '23503',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '23503'
    );

    -- Trocar o dono do vínculo: FK composta -> 23503.
    v_erro := null;
    begin
        update public.caderno_questoes
           set id_usuario = v_a_id
         where id_caderno = v_b_cad
           and id_questao = v_q
           and id_usuario = v_b_id;
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _f03_resultados values (
        'FK_bloqueia_troca_de_dono', '23503',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '23503'
    );

    -- ON DELETE CASCADE: apagar o caderno A remove o vínculo de A.
    delete from public.cadernos where id_caderno = v_a_cad;
    insert into _f03_resultados values (
        'delete_caderno_cascateia_vinculos', '0',
        (select count(*)::text from public.caderno_questoes where id_caderno = v_a_cad),
        (select count(*) from public.caderno_questoes where id_caderno = v_a_cad) = 0
    );

    -- O vínculo de B continua intacto.
    insert into _f03_resultados values (
        'vinculo_de_B_preservado', '1',
        (select count(*)::text from public.caderno_questoes where id_caderno = v_b_cad),
        (select count(*) from public.caderno_questoes where id_caderno = v_b_cad) = 1
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
from _f03_resultados;

rollback;
