-- ============================================================================
-- F-01 — Teste de isolamento da RLS de SELECT (2 usuários + anon sem JWT)
--
-- O que este script faz:
--   1. Cria, DENTRO DE UMA TRANSAÇÃO, dois usuários fictícios (A e B), um
--      simulado público e um privado para cada, questões, resultados,
--      histórico e comentários.
--   2. Consulta os dados como `anon` (sem JWT), como o aluno A e como o
--      aluno B, usando `set local role` + claims de JWT.
--   3. Verifica as views/RPC de conteúdo público e os metadados (nenhuma
--      coluna de dono/e-mail exposta).
--   4. Compara tudo com o esperado e devolve `passou = true/false` + a
--      lista de asserções.
--   5. Termina com ROLLBACK: nenhum dado de teste fica no banco.
--
-- Pré-requisito: existir pelo menos uma questão com status = 'publicada'
-- (o script usa uma questão real apenas como referência; nada é alterado).
--
-- Como rodar: cole no SQL Editor do Supabase ou execute via MCP
-- (`execute_sql`). Resultado esperado: passou = true e total = 40.
-- Se passou = false, a coluna `resultados` mostra esperado x obtido.
-- ============================================================================

begin;

create temp table _rls_f01_resultados (
    teste text primary key,
    valor bigint not null
) on commit drop;

create temp table _rls_f01_esperado (
    teste text primary key,
    esperado bigint not null
) on commit drop;

grant insert, select on _rls_f01_resultados to anon, authenticated;

-- ---------------------------------------------------------------------------
-- Fixtures (como postgres; revertidas no ROLLBACK)
-- ---------------------------------------------------------------------------

with a as (
    insert into public.usuarios (username, email, auth_id)
    values (
        'rls_f01_a_' || substr(md5(random()::text), 1, 10),
        'rls_f01_a_' || substr(md5(random()::text), 1, 10) || '@example.invalid',
        '11111111-1111-4111-8111-111111111111'
    )
    returning id
)
select set_config('rls_f01.a_id', id::text, true) from a;

with b as (
    insert into public.usuarios (username, email, auth_id)
    values (
        'rls_f01_b_' || substr(md5(random()::text), 1, 10),
        'rls_f01_b_' || substr(md5(random()::text), 1, 10) || '@example.invalid',
        '22222222-2222-4222-8222-222222222222'
    )
    returning id
)
select set_config('rls_f01.b_id', id::text, true) from b;

-- Questão pública usada como referência (nenhuma alteração nela).
select set_config('rls_f01.q_id', id_questao::text, true)
from public.questoes
where status = 'publicada'
order by id_questao
limit 1;

do $$
begin
    if current_setting('rls_f01.q_id', true) is null then
        raise exception 'test_rls_f01: nenhuma questão com status = publicada encontrada';
    end if;
end $$;

insert into public.historico_respostas (id_usuario, id_questao, is_correct)
values
    (current_setting('rls_f01.a_id'), current_setting('rls_f01.q_id')::int, true),
    (current_setting('rls_f01.b_id'), current_setting('rls_f01.q_id')::int, false);

with s as (
    insert into public.simulados (id_criador, titulo, eh_privado)
    values (current_setting('rls_f01.a_id')::int, 'rls_f01 A publico', false)
    returning id
)
select set_config('rls_f01.a_pub', id::text, true) from s;

with s as (
    insert into public.simulados (id_criador, titulo, eh_privado)
    values (current_setting('rls_f01.a_id')::int, 'rls_f01 A privado', true)
    returning id
)
select set_config('rls_f01.a_priv', id::text, true) from s;

with s as (
    insert into public.simulados (id_criador, titulo, eh_privado)
    values (current_setting('rls_f01.b_id')::int, 'rls_f01 B publico', false)
    returning id
)
select set_config('rls_f01.b_pub', id::text, true) from s;

with s as (
    insert into public.simulados (id_criador, titulo, eh_privado)
    values (current_setting('rls_f01.b_id')::int, 'rls_f01 B privado', true)
    returning id
)
select set_config('rls_f01.b_priv', id::text, true) from s;

insert into public.simulados_questoes (id_simulado, id_questao)
values
    (current_setting('rls_f01.a_pub')::uuid, current_setting('rls_f01.q_id')::int),
    (current_setting('rls_f01.a_priv')::uuid, current_setting('rls_f01.q_id')::int),
    (current_setting('rls_f01.b_pub')::uuid, current_setting('rls_f01.q_id')::int),
    (current_setting('rls_f01.b_priv')::uuid, current_setting('rls_f01.q_id')::int);

insert into public.simulados_resultados (id_simulado, id_usuario, nota, respostas_corretas, total_questoes)
values
    (current_setting('rls_f01.a_pub')::uuid, current_setting('rls_f01.a_id')::int, 10, 1, 1),
    (current_setting('rls_f01.a_priv')::uuid, current_setting('rls_f01.a_id')::int, 10, 1, 1),
    (current_setting('rls_f01.b_pub')::uuid, current_setting('rls_f01.b_id')::int, 5, 1, 1),
    (current_setting('rls_f01.b_priv')::uuid, current_setting('rls_f01.b_id')::int, 5, 1, 1);

with c as (
    insert into public.comentarios_questao (id_questao, id_usuario, nome_usuario, texto_comentario)
    values (
        current_setting('rls_f01.q_id')::int,
        current_setting('rls_f01.a_id'),
        'rls_f01_a',
        'rls_f01_comentario_a'
    )
    returning id_comentario
)
select set_config('rls_f01.a_comment', id_comentario::text, true) from c;

with c as (
    insert into public.comentarios_questao (id_questao, id_usuario, nome_usuario, texto_comentario)
    values (
        current_setting('rls_f01.q_id')::int,
        current_setting('rls_f01.b_id'),
        'rls_f01_b',
        'rls_f01_comentario_b'
    )
    returning id_comentario
)
select set_config('rls_f01.b_comment', id_comentario::text, true) from c;

-- ---------------------------------------------------------------------------
-- ANON (sem JWT): 0 linhas nas tabelas de aluno; sem grant nas views/RPC
-- privadas. A view de comentários é pública por desenho e deve funcionar.
-- ---------------------------------------------------------------------------
select set_config('request.jwt.claim.sub', '', true);
select set_config('request.jwt.claims', '{"role":"anon"}', true);
set local role anon;

insert into _rls_f01_resultados values
    ('anon_usuarios', (select count(*) from public.usuarios)),
    ('anon_historico', (select count(*) from public.historico_respostas)),
    ('anon_simulados', (select count(*) from public.simulados)),
    ('anon_simulados_resultados', (select count(*) from public.simulados_resultados)),
    ('anon_comentarios_tabela', (select count(*) from public.comentarios_questao)),
    ('anon_view_comentarios', (
        select count(*) from public.view_comentarios_publicos
        where id_comentario in (
            current_setting('rls_f01.a_comment')::uuid,
            current_setting('rls_f01.b_comment')::uuid
        )
    ));
reset role;

insert into _rls_f01_resultados values
    ('anon_pode_view_simulados', case
        when has_table_privilege('anon', 'public.view_simulados_publicos', 'select') then 1 else 0
    end),
    ('anon_pode_view_questoes_publicas', case
        when has_table_privilege('anon', 'public.view_simulados_questoes_publicas', 'select') then 1 else 0
    end),
    ('anon_pode_rpc_ranking', case
        when has_function_privilege('anon', 'public.ranking_simulado(uuid)', 'execute') then 1 else 0
    end);

-- ---------------------------------------------------------------------------
-- ALUNO A
-- ---------------------------------------------------------------------------
select set_config('request.jwt.claim.sub', '11111111-1111-4111-8111-111111111111', true);
select set_config(
    'request.jwt.claims',
    '{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated"}',
    true
);
set local role authenticated;

insert into _rls_f01_resultados values
    ('A_usuarios', (select count(*) from public.usuarios)),
    ('A_historico_proprio', (
        select count(*) from public.historico_respostas
        where id_usuario = current_setting('rls_f01.a_id')
    )),
    ('A_historico_B', (
        select count(*) from public.historico_respostas
        where id_usuario = current_setting('rls_f01.b_id')
    )),
    ('A_simulados', (select count(*) from public.simulados)),
    ('A_simulados_B', (
        select count(*) from public.simulados
        where id_criador = current_setting('rls_f01.b_id')::int
    )),
    ('A_simulados_questoes_proprias', (select count(*) from public.simulados_questoes)),
    ('A_simulados_questoes_B', (
        select count(*) from public.simulados_questoes
        where id_simulado = current_setting('rls_f01.b_pub')::uuid
    )),
    ('A_comentarios_tabela', (select count(*) from public.comentarios_questao)),
    ('A_comentarios_B', (
        select count(*) from public.comentarios_questao
        where id_usuario = current_setting('rls_f01.b_id')
    )),
    ('A_view_comentarios', (
        select count(*) from public.view_comentarios_publicos
        where id_comentario in (
            current_setting('rls_f01.a_comment')::uuid,
            current_setting('rls_f01.b_comment')::uuid
        )
    )),
    ('A_view_simulados', (
        select count(*) from public.view_simulados_publicos
        where id in (
            current_setting('rls_f01.a_pub')::uuid,
            current_setting('rls_f01.b_pub')::uuid
        )
    )),
    ('A_view_simulados_eh_meu', (
        select count(*) from public.view_simulados_publicos
        where id = current_setting('rls_f01.a_pub')::uuid
          and eh_meu
    )),
    ('A_view_questoes_publicas', (
        select count(*) from public.view_simulados_questoes_publicas
        where id_simulado in (
            current_setting('rls_f01.a_pub')::uuid,
            current_setting('rls_f01.b_pub')::uuid
        )
    )),
    ('A_ranking_B_publico', (
        select count(*) from public.ranking_simulado(current_setting('rls_f01.b_pub')::uuid)
    )),
    ('A_ranking_B_privado', (
        select count(*) from public.ranking_simulado(current_setting('rls_f01.b_priv')::uuid)
    )),
    ('A_ranking_A_privado', (
        select count(*) from public.ranking_simulado(current_setting('rls_f01.a_priv')::uuid)
    ));
reset role;

-- ---------------------------------------------------------------------------
-- ALUNO B
-- ---------------------------------------------------------------------------
select set_config('request.jwt.claim.sub', '22222222-2222-4222-8222-222222222222', true);
select set_config(
    'request.jwt.claims',
    '{"sub":"22222222-2222-4222-8222-222222222222","role":"authenticated"}',
    true
);
set local role authenticated;

insert into _rls_f01_resultados values
    ('B_usuarios', (select count(*) from public.usuarios)),
    ('B_historico_A', (
        select count(*) from public.historico_respostas
        where id_usuario = current_setting('rls_f01.a_id')
    )),
    ('B_simulados', (select count(*) from public.simulados)),
    ('B_simulados_A', (
        select count(*) from public.simulados
        where id_criador = current_setting('rls_f01.a_id')::int
    )),
    ('B_comentarios_A', (
        select count(*) from public.comentarios_questao
        where id_usuario = current_setting('rls_f01.a_id')
    )),
    ('B_view_comentarios', (
        select count(*) from public.view_comentarios_publicos
        where id_comentario in (
            current_setting('rls_f01.a_comment')::uuid,
            current_setting('rls_f01.b_comment')::uuid
        )
    )),
    ('B_view_simulados', (
        select count(*) from public.view_simulados_publicos
        where id in (
            current_setting('rls_f01.a_pub')::uuid,
            current_setting('rls_f01.b_pub')::uuid
        )
    )),
    ('B_view_simulados_eh_meu', (
        select count(*) from public.view_simulados_publicos
        where id = current_setting('rls_f01.b_pub')::uuid
          and eh_meu
    )),
    ('B_ranking_A_publico', (
        select count(*) from public.ranking_simulado(current_setting('rls_f01.a_pub')::uuid)
    )),
    ('B_ranking_A_privado', (
        select count(*) from public.ranking_simulado(current_setting('rls_f01.a_priv')::uuid)
    )),
    ('B_ranking_B_privado', (
        select count(*) from public.ranking_simulado(current_setting('rls_f01.b_priv')::uuid)
    ));
reset role;

-- ---------------------------------------------------------------------------
-- Metadados: as views públicas não expõem colunas de dono/e-mail.
-- ---------------------------------------------------------------------------
insert into _rls_f01_resultados values
    ('view_comentarios_tem_id_usuario', (
        select count(*) from information_schema.columns
        where table_schema = 'public'
          and table_name = 'view_comentarios_publicos'
          and column_name in ('id_usuario', 'auth_id', 'email')
    )),
    ('view_simulados_tem_id_criador', (
        select count(*) from information_schema.columns
        where table_schema = 'public'
          and table_name = 'view_simulados_publicos'
          and column_name in ('id_criador', 'id_usuario', 'auth_id', 'email')
    )),
    ('authenticated_pode_view_simulados', case
        when has_table_privilege('authenticated', 'public.view_simulados_publicos', 'select') then 1 else 0
    end),
    ('authenticated_pode_rpc_ranking', case
        when has_function_privilege('authenticated', 'public.ranking_simulado(uuid)', 'execute') then 1 else 0
    end);

-- ---------------------------------------------------------------------------
-- Expectativas
-- ---------------------------------------------------------------------------
insert into _rls_f01_esperado values
    ('anon_usuarios', 0),
    ('anon_historico', 0),
    ('anon_simulados', 0),
    ('anon_simulados_resultados', 0),
    ('anon_comentarios_tabela', 0),
    ('anon_view_comentarios', 2),
    ('anon_pode_view_simulados', 0),
    ('anon_pode_view_questoes_publicas', 0),
    ('anon_pode_rpc_ranking', 0),

    ('A_usuarios', 1),
    ('A_historico_proprio', 1),
    ('A_historico_B', 0),
    ('A_simulados', 2),
    ('A_simulados_B', 0),
    ('A_simulados_questoes_proprias', 2),
    ('A_simulados_questoes_B', 0),
    ('A_comentarios_tabela', 1),
    ('A_comentarios_B', 0),
    ('A_view_comentarios', 2),
    ('A_view_simulados', 2),
    ('A_view_simulados_eh_meu', 1),
    ('A_view_questoes_publicas', 2),
    ('A_ranking_B_publico', 1),
    ('A_ranking_B_privado', 0),
    ('A_ranking_A_privado', 1),

    ('B_usuarios', 1),
    ('B_historico_A', 0),
    ('B_simulados', 2),
    ('B_simulados_A', 0),
    ('B_comentarios_A', 0),
    ('B_view_comentarios', 2),
    ('B_view_simulados', 2),
    ('B_view_simulados_eh_meu', 1),
    ('B_ranking_A_publico', 1),
    ('B_ranking_A_privado', 0),
    ('B_ranking_B_privado', 1),

    ('view_comentarios_tem_id_usuario', 0),
    ('view_simulados_tem_id_criador', 0),
    ('authenticated_pode_view_simulados', 1),
    ('authenticated_pode_rpc_ranking', 1);

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
from _rls_f01_esperado e
join _rls_f01_resultados r using (teste);

-- Nada do que foi criado acima fica no banco.
rollback;
