-- ============================================================================
-- F-11 — Teste transacional: allowlist de username e limites do comentário.
--
-- Verifica, no banco:
--   * username válido passa;
--   * username com HTML falha (23514);
--   * username com 31 caracteres falha (23514);
--   * comentário válido passa;
--   * nome_usuario com HTML falha (23514), mesmo em INSERT direto;
--   * texto vazio/só espaços falha (23514);
--   * texto com 1001 caracteres falha (23514);
--   * texto com caractere de controle falha (23514).
--
-- Resultado esperado: passou = true, total = 8, falhas = 0.
-- Termina com ROLLBACK: nenhum dado de teste fica no banco.
-- ============================================================================

begin;

create temp table _f11_resultados (
    teste text primary key,
    esperado text not null,
    obtido text not null,
    passou boolean not null
) on commit drop;

do $$
declare
    v_qid int;
    v_erro text;
    v_username text;
begin
    select id_questao into v_qid
    from public.questoes
    order by id_questao
    limit 1;

    if v_qid is null then
        raise exception 'test_f11: é preciso existir ao menos uma questão';
    end if;

    v_username := 'f11_' || substr(md5(random()::text), 1, 8);

    -- -----------------------------------------------------------------------
    -- 1. Username válido
    -- -----------------------------------------------------------------------
    v_erro := null;
    begin
        insert into public.usuarios (username, email)
        values (v_username, v_username || '@example.invalid');
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _f11_resultados values (
        'username_valido', 'OK',
        coalesce(v_erro, 'OK'), coalesce(v_erro, 'OK') = 'OK'
    );

    -- -----------------------------------------------------------------------
    -- 2. Username com HTML
    -- -----------------------------------------------------------------------
    v_erro := null;
    begin
        insert into public.usuarios (username, email)
        values (
            '<img src=x onerror=alert(1)>',
            'f11_xss_' || substr(md5(random()::text), 1, 8) || '@example.invalid'
        );
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _f11_resultados values (
        'username_com_html', '23514',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '23514'
    );

    -- -----------------------------------------------------------------------
    -- 3. Username com 31 caracteres
    -- -----------------------------------------------------------------------
    v_erro := null;
    begin
        insert into public.usuarios (username, email)
        values (
            repeat('a', 31),
            'f11_longo_' || substr(md5(random()::text), 1, 8) || '@example.invalid'
        );
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _f11_resultados values (
        'username_longo', '23514',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '23514'
    );

    -- -----------------------------------------------------------------------
    -- 4. Comentário válido (o texto pode conter < e >; a saída é que codifica)
    -- -----------------------------------------------------------------------
    v_erro := null;
    begin
        insert into public.comentarios_questao
            (id_questao, id_usuario, nome_usuario, texto_comentario)
        values
            (v_qid, 'f11_user', v_username, 'Comentário com <b>marcação</b> literal');
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _f11_resultados values (
        'comentario_valido', 'OK',
        coalesce(v_erro, 'OK'), coalesce(v_erro, 'OK') = 'OK'
    );

    -- -----------------------------------------------------------------------
    -- 5. Nome do comentário com HTML (INSERT direto via PostgREST)
    -- -----------------------------------------------------------------------
    v_erro := null;
    begin
        insert into public.comentarios_questao
            (id_questao, id_usuario, nome_usuario, texto_comentario)
        values
            (v_qid, 'f11_user', '<img src=x onerror=alert(1)>', 'texto normal');
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _f11_resultados values (
        'comentario_nome_com_html', '23514',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '23514'
    );

    -- -----------------------------------------------------------------------
    -- 6. Texto vazio / só espaços
    -- -----------------------------------------------------------------------
    v_erro := null;
    begin
        insert into public.comentarios_questao
            (id_questao, id_usuario, nome_usuario, texto_comentario)
        values (v_qid, 'f11_user', v_username, '   ');
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _f11_resultados values (
        'comentario_texto_vazio', '23514',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '23514'
    );

    -- -----------------------------------------------------------------------
    -- 7. Texto com 1001 caracteres
    -- -----------------------------------------------------------------------
    v_erro := null;
    begin
        insert into public.comentarios_questao
            (id_questao, id_usuario, nome_usuario, texto_comentario)
        values (v_qid, 'f11_user', v_username, repeat('x', 1001));
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _f11_resultados values (
        'comentario_texto_longo', '23514',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '23514'
    );

    -- -----------------------------------------------------------------------
    -- 8. Texto com caractere de controle
    -- -----------------------------------------------------------------------
    v_erro := null;
    begin
        insert into public.comentarios_questao
            (id_questao, id_usuario, nome_usuario, texto_comentario)
        values (v_qid, 'f11_user', v_username, E'texto\x01com controle');
    exception when others then
        v_erro := sqlstate;
    end;
    insert into _f11_resultados values (
        'comentario_texto_com_controle', '23514',
        coalesce(v_erro, 'OK'), coalesce(v_erro, '') = '23514'
    );
end $$;

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
from _f11_resultados;

rollback;
