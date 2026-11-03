-- ============================================================================
-- F-11 — Formato de username e limite do comentário (defesa em profundidade)
--
-- A correção principal do XSS armazenado é na saída: o feed de comentários
-- monta o DOM com textContent/createTextNode (static/js/questoes_common.js),
-- nunca com innerHTML/template literal. Esta migration coloca no banco a
-- mesma allowlist aplicada pelo servidor (utils.validar_username) e limita o
-- texto do comentário, para que um INSERT direto via PostgREST/JWT também não
-- consiga gravar um nome com HTML ou um texto vazio/ilimitado.
--
-- Observação: o TEXTO do comentário continua sendo armazenado como o aluno
-- digitou (inclusive < e >, que podem ser legítimos em comparações). A defesa
-- contra HTML no texto é a codificação de saída no cliente; o banco apenas
-- rejeita vazio, excesso de tamanho e caracteres de controle.
--
-- IDEMPOTENTE: pode ser reaplicada. Aplicar via MCP (apply_migration) ou SQL
-- Editor. Teste transacional: docs/migrations/test_f11.sql.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 0. Falha cedo se houver dado legado fora do formato. Não reescreve o
--    username de ninguém: a normalização é uma decisão explícita do operador.
--    (Produção em 2026-11-03: 1 usuário, 0 comentários, ambos dentro do padrão.)
-- ----------------------------------------------------------------------------
do $$
begin
    if exists (
        select 1
        from public.usuarios
        where username !~ '^[[:alnum:] ._-]{2,30}$'
    ) then
        raise exception
            'F-11: existe username fora do formato (2-30; letras/números/espaço/ponto/hífen/underscore); corrija antes de aplicar';
    end if;

    if exists (
        select 1
        from public.comentarios_questao
        where nome_usuario !~ '^[[:alnum:] ._-]{2,30}$'
           or char_length(texto_comentario) not between 1 and 1000
           or btrim(texto_comentario) = ''
           or texto_comentario ~ '[[:cntrl:]]'
    ) then
        raise exception
            'F-11: existe comentário legado com nome/texto inválido; corrija antes de aplicar';
    end if;
end $$;

-- ----------------------------------------------------------------------------
-- 1. Username do aluno (fonte do nome exibido nos comentários).
-- ----------------------------------------------------------------------------
alter table public.usuarios
    drop constraint if exists usuarios_username_formato;
alter table public.usuarios
    add constraint usuarios_username_formato
    check (username ~ '^[[:alnum:] ._-]{2,30}$');

-- ----------------------------------------------------------------------------
-- 2. Cópia denormalizada do nome no comentário. Sem esta constraint, um
--    INSERT direto via PostgREST poderia gravar nome_usuario com HTML mesmo
--    com o username do perfil limpo.
-- ----------------------------------------------------------------------------
alter table public.comentarios_questao
    drop constraint if exists comentarios_nome_usuario_formato;
alter table public.comentarios_questao
    add constraint comentarios_nome_usuario_formato
    check (nome_usuario ~ '^[[:alnum:] ._-]{2,30}$');

-- ----------------------------------------------------------------------------
-- 3. Texto do comentário: não vazio, até 1000 caracteres e sem controles.
-- ----------------------------------------------------------------------------
alter table public.comentarios_questao
    drop constraint if exists comentarios_texto_valido;
alter table public.comentarios_questao
    add constraint comentarios_texto_valido
    check (
        char_length(texto_comentario) between 1 and 1000
        and btrim(texto_comentario) <> ''
        and texto_comentario !~ '[[:cntrl:]]'
    );
