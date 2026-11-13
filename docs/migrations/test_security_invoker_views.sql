-- ============================================================================
-- Lint 0010 — Teste das views públicas com security_invoker
--
-- O que este script faz:
--   1. Cria, DENTRO DE UMA TRANSAÇÃO, dois usuários fictícios (A e B), um
--      simulado público e um privado para cada, questões, comentários e
--      vínculos simulado/questão.
--   2. Verifica os metadados: os wrappers de `public` são security_invoker,
--      as views privilegiadas de `private` existem e nenhum wrapper expõe
--      id_usuario, id_criador, auth_id ou e-mail.
--   3. Consulta como `anon` (sem JWT) e como A/B (com JWT), conferindo que o
--      filtro de conteúdo público e o `eh_meu` continuam corretos.
--   4. Compara tudo com o esperado e devolve `passou = true/false`.
--   5. Termina com ROLLBACK: nenhum dado de teste fica no banco.
--
-- Pré-requisitos: existirem pelo menos duas questões com status='publicada'
-- (o script usa questões reais como referência; a segunda é marcada como
-- arquivada apenas dentro da transação e o ROLLBACK desfaz).
--
-- Como rodar: cole no SQL Editor do Supabase ou execute via MCP
-- (`execute_sql`). Resultado esperado: passou = true e total = 26.
-- ============================================================================

begin;

create temp table _sv_resultados (
    teste text primary key,
    valor bigint not null
) on commit drop;

create temp table _sv_esperado (
    teste text primary key,
    esperado bigint not null
) on commit drop;

grant insert, select on _sv_resultados to anon, authenticated;

-- ---------------------------------------------------------------------------
-- Fixtures (como postgres; revertidas no ROLLBACK)
-- ---------------------------------------------------------------------------

with a as (
    insert into public.usuarios (username, email, auth_id)
    values (
        'sv_a_' || substr(md5(random()::text), 1, 10),
        'sv_a_' || substr(md5(random()::text), 1, 10) || '@example.invalid',
        '33333333-3333-4333-8333-333333333333'
    )
    returning id
)
select set_config('sv.a_id', id::text, true) from a;

with b as (
    insert into public.usuarios (username, email, auth_id)
    values (
        'sv_b_' || substr(md5(random()::text), 1, 10),
        'sv_b_' || substr(md5(random()::text), 1, 10) || '@example.invalid',
        '44444444-4444-4444-8444-444444444444'
    )
    returning id
)
select set_config('sv.b_id', id::text, true) from b;

select set_config('sv.q_pub', id_questao::text, true)
from public.questoes
where status = 'publicada'
order by id_questao
limit 1;

select set_config('sv.q_draft', id_questao::text, true)
from public.questoes
where status = 'publicada'
  and id_questao <> current_setting('sv.q_pub')::int
order by id_questao
limit 1;

do $$
begin
    if current_setting('sv.q_pub', true) is null
       or current_setting('sv.q_draft', true) is null then
        raise exception 'test_security_invoker: são necessárias duas questões publicadas';
    end if;
end $$;

-- A segunda questão vira arquivada apenas nesta transação (status fora de
-- 'publicada' é excluído pela view pública).
update public.questoes
set status = 'arquivada'
where id_questao = current_setting('sv.q_draft')::int;

with c as (
    insert into public.comentarios_questao
        (id_questao, id_usuario, nome_usuario, texto_comentario)
    values (
        current_setting('sv.q_pub')::int,
        current_setting('sv.a_id'),
        'sv_a',
        'sv_comentario_a_publicado'
    )
    returning id_comentario
)
select set_config('sv.c_pub_a', id_comentario::text, true) from c;

with c as (
    insert into public.comentarios_questao
        (id_questao, id_usuario, nome_usuario, texto_comentario)
    values (
        current_setting('sv.q_pub')::int,
        current_setting('sv.b_id'),
        'sv_b',
        'sv_comentario_b_publicado'
    )
    returning id_comentario
)
select set_config('sv.c_pub_b', id_comentario::text, true) from c;

with c as (
    insert into public.comentarios_questao
        (id_questao, id_usuario, nome_usuario, texto_comentario)
    values (
        current_setting('sv.q_draft')::int,
        current_setting('sv.a_id'),
        'sv_a',
        'sv_comentario_rascunho'
    )
    returning id_comentario
)
select set_config('sv.c_draft', id_comentario::text, true) from c;

with s as (
    insert into public.simulados (id_criador, titulo, eh_privado)
    values (current_setting('sv.a_id')::int, 'sv A publico', false)
    returning id
)
select set_config('sv.a_pub', id::text, true) from s;

with s as (
    insert into public.simulados (id_criador, titulo, eh_privado)
    values (current_setting('sv.a_id')::int, 'sv A privado', true)
    returning id
)
select set_config('sv.a_priv', id::text, true) from s;

with s as (
    insert into public.simulados (id_criador, titulo, eh_privado)
    values (current_setting('sv.b_id')::int, 'sv B publico', false)
    returning id
)
select set_config('sv.b_pub', id::text, true) from s;

with s as (
    insert into public.simulados (id_criador, titulo, eh_privado)
    values (current_setting('sv.b_id')::int, 'sv B privado', true)
    returning id
)
select set_config('sv.b_priv', id::text, true) from s;

insert into public.simulados_questoes (id_simulado, id_questao)
values
    (current_setting('sv.a_pub')::uuid, current_setting('sv.q_pub')::int),
    (current_setting('sv.a_priv')::uuid, current_setting('sv.q_pub')::int),
    (current_setting('sv.b_pub')::uuid, current_setting('sv.q_pub')::int),
    (current_setting('sv.b_priv')::uuid, current_setting('sv.q_pub')::int);

-- ---------------------------------------------------------------------------
-- Metadados: wrappers invoker + views privilegiadas no schema private
-- ---------------------------------------------------------------------------
insert into _sv_resultados values
    ('public_comentarios_invoker', case when exists (
        select 1 from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public'
          and c.relname = 'view_comentarios_publicos'
          and 'security_invoker=true' = any(c.reloptions)
    ) then 1 else 0 end),
    ('public_simulados_invoker', case when exists (
        select 1 from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public'
          and c.relname = 'view_simulados_publicos'
          and 'security_invoker=true' = any(c.reloptions)
    ) then 1 else 0 end),
    ('public_questoes_invoker', case when exists (
        select 1 from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public'
          and c.relname = 'view_simulados_questoes_publicas'
          and 'security_invoker=true' = any(c.reloptions)
    ) then 1 else 0 end),
    ('private_comentarios_existe', case
        when to_regclass('private.view_comentarios_publicos') is not null then 1 else 0 end),
    ('private_simulados_existe', case
        when to_regclass('private.view_simulados_publicos') is not null then 1 else 0 end),
    ('private_questoes_existe', case
        when to_regclass('private.view_simulados_questoes_publicas') is not null then 1 else 0 end),
    ('private_comentarios_definer', case when exists (
        select 1 from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'private'
          and c.relname = 'view_comentarios_publicos'
          and 'security_invoker=false' = any(c.reloptions)
    ) then 1 else 0 end),
    ('private_simulados_definer', case when exists (
        select 1 from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'private'
          and c.relname = 'view_simulados_publicos'
          and 'security_invoker=false' = any(c.reloptions)
    ) then 1 else 0 end),
    ('private_questoes_definer', case when exists (
        select 1 from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'private'
          and c.relname = 'view_simulados_questoes_publicas'
          and 'security_invoker=false' = any(c.reloptions)
    ) then 1 else 0 end),
    ('public_comentarios_sem_colunas_sensiveis', (
        select count(*) from information_schema.columns
        where table_schema = 'public'
          and table_name = 'view_comentarios_publicos'
          and column_name in ('id_usuario', 'auth_id', 'email')
    )),
    ('public_simulados_sem_colunas_sensiveis', (
        select count(*) from information_schema.columns
        where table_schema = 'public'
          and table_name = 'view_simulados_publicos'
          and column_name in ('id_criador', 'id_usuario', 'auth_id', 'email')
    )),
    ('anon_pode_view_comentarios', case
        when has_table_privilege('anon', 'public.view_comentarios_publicos', 'select') then 1 else 0 end),
    ('anon_pode_view_simulados', case
        when has_table_privilege('anon', 'public.view_simulados_publicos', 'select') then 1 else 0 end),
    ('anon_pode_view_questoes', case
        when has_table_privilege('anon', 'public.view_simulados_questoes_publicas', 'select') then 1 else 0 end),
    ('authenticated_pode_view_comentarios', case
        when has_table_privilege('authenticated', 'public.view_comentarios_publicos', 'select') then 1 else 0 end),
    ('authenticated_pode_view_simulados', case
        when has_table_privilege('authenticated', 'public.view_simulados_publicos', 'select') then 1 else 0 end),
    ('authenticated_pode_view_questoes', case
        when has_table_privilege('authenticated', 'public.view_simulados_questoes_publicas', 'select') then 1 else 0 end);

-- ---------------------------------------------------------------------------
-- ANON (sem JWT): só o feed de comentários é público; rascunho não aparece.
-- ---------------------------------------------------------------------------
select set_config('request.jwt.claim.sub', '', true);
select set_config('request.jwt.claims', '{"role":"anon"}', true);
set local role anon;

insert into _sv_resultados values
    ('anon_comentarios_publicados', (
        select count(*) from public.view_comentarios_publicos
        where id_comentario in (
            current_setting('sv.c_pub_a')::uuid,
            current_setting('sv.c_pub_b')::uuid,
            current_setting('sv.c_draft')::uuid
        )
    ));
reset role;

-- ---------------------------------------------------------------------------
-- ALUNO A
-- ---------------------------------------------------------------------------
select set_config('request.jwt.claim.sub', '33333333-3333-4333-8333-333333333333', true);
select set_config(
    'request.jwt.claims',
    '{"sub":"33333333-3333-4333-8333-333333333333","role":"authenticated"}',
    true
);
set local role authenticated;

insert into _sv_resultados values
    ('A_comentarios_publicados', (
        select count(*) from public.view_comentarios_publicos
        where id_comentario in (
            current_setting('sv.c_pub_a')::uuid,
            current_setting('sv.c_pub_b')::uuid,
            current_setting('sv.c_draft')::uuid
        )
    )),
    ('A_simulados_publicos', (
        select count(*) from public.view_simulados_publicos
        where id in (
            current_setting('sv.a_pub')::uuid,
            current_setting('sv.a_priv')::uuid,
            current_setting('sv.b_pub')::uuid,
            current_setting('sv.b_priv')::uuid
        )
    )),
    ('A_simulados_privado_visivel', (
        select count(*) from public.view_simulados_publicos
        where id = current_setting('sv.a_priv')::uuid
    )),
    ('A_simulados_eh_meu', (
        select count(*) from public.view_simulados_publicos
        where id = current_setting('sv.a_pub')::uuid
          and eh_meu
    )),
    ('A_questoes_publicas', (
        select count(*) from public.view_simulados_questoes_publicas
        where id_simulado in (
            current_setting('sv.a_pub')::uuid,
            current_setting('sv.a_priv')::uuid,
            current_setting('sv.b_pub')::uuid,
            current_setting('sv.b_priv')::uuid
        )
    ));
reset role;

-- ---------------------------------------------------------------------------
-- ALUNO B
-- ---------------------------------------------------------------------------
select set_config('request.jwt.claim.sub', '44444444-4444-4444-8444-444444444444', true);
select set_config(
    'request.jwt.claims',
    '{"sub":"44444444-4444-4444-8444-444444444444","role":"authenticated"}',
    true
);
set local role authenticated;

insert into _sv_resultados values
    ('B_simulados_publicos', (
        select count(*) from public.view_simulados_publicos
        where id in (
            current_setting('sv.a_pub')::uuid,
            current_setting('sv.a_priv')::uuid,
            current_setting('sv.b_pub')::uuid,
            current_setting('sv.b_priv')::uuid
        )
    )),
    ('B_simulados_eh_meu', (
        select count(*) from public.view_simulados_publicos
        where id = current_setting('sv.b_pub')::uuid
          and eh_meu
    )),
    ('B_questoes_publicas', (
        select count(*) from public.view_simulados_questoes_publicas
        where id_simulado in (
            current_setting('sv.a_pub')::uuid,
            current_setting('sv.a_priv')::uuid,
            current_setting('sv.b_pub')::uuid,
            current_setting('sv.b_priv')::uuid
        )
    ));
reset role;

-- ---------------------------------------------------------------------------
-- Expectativas
-- ---------------------------------------------------------------------------
insert into _sv_esperado values
    ('public_comentarios_invoker', 1),
    ('public_simulados_invoker', 1),
    ('public_questoes_invoker', 1),
    ('private_comentarios_existe', 1),
    ('private_simulados_existe', 1),
    ('private_questoes_existe', 1),
    ('private_comentarios_definer', 1),
    ('private_simulados_definer', 1),
    ('private_questoes_definer', 1),
    ('public_comentarios_sem_colunas_sensiveis', 0),
    ('public_simulados_sem_colunas_sensiveis', 0),
    ('anon_pode_view_comentarios', 1),
    ('anon_pode_view_simulados', 0),
    ('anon_pode_view_questoes', 0),
    ('authenticated_pode_view_comentarios', 1),
    ('authenticated_pode_view_simulados', 1),
    ('authenticated_pode_view_questoes', 1),
    ('anon_comentarios_publicados', 2),
    ('A_comentarios_publicados', 2),
    ('A_simulados_publicos', 2),
    ('A_simulados_privado_visivel', 0),
    ('A_simulados_eh_meu', 1),
    ('A_questoes_publicas', 2),
    ('B_simulados_publicos', 2),
    ('B_simulados_eh_meu', 1),
    ('B_questoes_publicas', 2);

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
from _sv_esperado e
join _sv_resultados r using (teste);

-- Nada do que foi criado acima fica no banco.
rollback;
