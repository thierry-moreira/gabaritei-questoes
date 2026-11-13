-- ============================================================================
-- F-01 — RLS de SELECT owner-only nas tabelas de dados do aluno
-- + separação explícita do conteúdo público (comentários, simulados públicos
--   e ranking) em views/função de leitura segura.
--
-- Contexto: a anon key é pública e vai embarcada no cliente. Sem JWT, o papel
-- `anon` não pode ler nenhuma linha das tabelas de dados do aluno. Com JWT,
-- cada aluno lê apenas as próprias linhas. Conteúdo que é público por desenho
-- (comentários de questão, simulados com eh_privado=false e seus rankings)
-- passa por views/função que expõem SOMENTE colunas públicas — nunca
-- id_usuario, e-mail ou auth_id.
--
-- IDEMPOTENTE: pode ser reaplicada. Aplicar via Supabase SQL Editor ou MCP
-- (apply_migration). Teste de isolamento: docs/migrations/test_rls_f01.sql.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SELECT owner-only nas 16 tabelas de dados do aluno
--    (as policies já existiam com esse desenho desde
--     `consolidar_rls_select_unico_dados_aluno`; recriadas aqui para que a
--     migration fique versionada neste repositório e não dependa de drift).
-- ----------------------------------------------------------------------------

-- usuarios: dono pelo vínculo auth.users -> usuarios.auth_id. A cláusula do
-- legado (auth_id IS NULL) é necessária para o 1º login pós-Auth: o UPDATE de
-- re-link só enxerga a linha se o e-mail confirmado do JWT bater com o e-mail
-- da linha, caso contrário o Postgres afeta 0 linhas silenciosamente.
drop policy if exists anon_le_dados_aluno on public.usuarios;
create policy anon_le_dados_aluno on public.usuarios
    for select to anon, authenticated
    using (
        (select auth.uid()) = auth_id
        or (
            public.eh_app_aluno()
            and auth_id is null
            and lower(email) = lower((select auth.jwt()) ->> 'email')
        )
    );

-- historico_respostas.id_usuario é text (legado) -> overload text de
-- eh_dono_do_aluno.
drop policy if exists anon_le_dados_aluno on public.historico_respostas;
create policy anon_le_dados_aluno on public.historico_respostas
    for select to anon, authenticated
    using (public.eh_dono_do_aluno(id_usuario));

drop policy if exists anon_le_dados_aluno on public.comentarios_questao;
create policy anon_le_dados_aluno on public.comentarios_questao
    for select to anon, authenticated
    using (public.eh_dono_do_aluno(id_usuario));

drop policy if exists anon_le_dados_aluno on public.flashcards;
create policy anon_le_dados_aluno on public.flashcards
    for select to anon, authenticated
    using (public.eh_dono_do_aluno(id_usuario));

drop policy if exists anon_le_dados_aluno on public.flashcard_categorias;
create policy anon_le_dados_aluno on public.flashcard_categorias
    for select to anon, authenticated
    using (public.eh_dono_do_aluno(id_usuario));

drop policy if exists anon_le_dados_aluno on public.resumos_estudo;
create policy anon_le_dados_aluno on public.resumos_estudo
    for select to anon, authenticated
    using (public.eh_dono_do_aluno(id_usuario));

drop policy if exists anon_le_dados_aluno on public.cadernos;
create policy anon_le_dados_aluno on public.cadernos
    for select to anon, authenticated
    using (public.eh_dono_do_aluno(id_usuario));

drop policy if exists anon_le_dados_aluno on public.caderno_questoes;
create policy anon_le_dados_aluno on public.caderno_questoes
    for select to anon, authenticated
    using (public.eh_dono_do_aluno(id_usuario));

drop policy if exists anon_le_dados_aluno on public.filtros_salvos;
create policy anon_le_dados_aluno on public.filtros_salvos
    for select to anon, authenticated
    using (public.eh_dono_do_aluno(id_usuario));

drop policy if exists anon_le_dados_aluno on public.simulados;
create policy anon_le_dados_aluno on public.simulados
    for select to anon, authenticated
    using (public.eh_dono_do_aluno(id_criador));

-- O dono do simulado_questoes é o dono do simulado pai. A subconsulta em
-- simulados também passa pelo RLS owner-only; para o dono a linha é visível.
drop policy if exists anon_le_dados_aluno on public.simulados_questoes;
create policy anon_le_dados_aluno on public.simulados_questoes
    for select to anon, authenticated
    using (
        exists (
            select 1
            from public.simulados s
            where s.id = simulados_questoes.id_simulado
              and public.eh_dono_do_aluno(s.id_criador)
        )
    );

drop policy if exists anon_le_dados_aluno on public.simulados_resultados;
create policy anon_le_dados_aluno on public.simulados_resultados
    for select to anon, authenticated
    using (public.eh_dono_do_aluno(id_usuario));

drop policy if exists anon_le_dados_aluno on public.editais_ciclo;
create policy anon_le_dados_aluno on public.editais_ciclo
    for select to anon, authenticated
    using (public.eh_dono_do_aluno(id_usuario));

drop policy if exists anon_le_dados_aluno on public.editais_materias;
create policy anon_le_dados_aluno on public.editais_materias
    for select to anon, authenticated
    using (public.eh_dono_do_aluno(id_usuario));

drop policy if exists anon_le_dados_aluno on public.editais_topicos;
create policy anon_le_dados_aluno on public.editais_topicos
    for select to anon, authenticated
    using (public.eh_dono_do_aluno(id_usuario));

drop policy if exists anon_le_dados_aluno on public.editais_progresso;
create policy anon_le_dados_aluno on public.editais_progresso
    for select to anon, authenticated
    using (public.eh_dono_do_aluno(id_usuario));

-- ----------------------------------------------------------------------------
-- 2. Defesa em profundidade nos grants
--    RLS não se aplica a TRUNCATE; nenhum cliente do app precisa dele.
--    Escrita do app sempre sai com JWT (papel authenticated) + x-app-token;
--    o papel anon não precisa de INSERT/UPDATE/DELETE nas tabelas privadas.
--    O SELECT de anon é mantido para preservar o comportamento do
--    load_user (200 com 0 linhas em vez de permission denied) — quem barra
--    as linhas é a policy owner-only acima.
-- ----------------------------------------------------------------------------
revoke truncate on all tables in schema public from anon, authenticated;

revoke insert, update, delete on table
    public.usuarios,
    public.historico_respostas,
    public.comentarios_questao,
    public.flashcards,
    public.flashcard_categorias,
    public.resumos_estudo,
    public.cadernos,
    public.caderno_questoes,
    public.filtros_salvos,
    public.simulados,
    public.simulados_questoes,
    public.simulados_resultados,
    public.editais_ciclo,
    public.editais_materias,
    public.editais_topicos,
    public.editais_progresso
from anon;

-- ----------------------------------------------------------------------------
-- 3. Conteúdo público separado dos dados do aluno
--    Views rodam como o dono (postgres) e, por definição, não aplicam o RLS
--    das tabelas-base. Por isso cada uma expõe apenas colunas públicas e
--    filtra explicitamente o que é público. Grants são apenas SELECT.
--
--    ATENÇÃO (lint 0010): este desenho original criava views SECURITY DEFINER
--    no schema exposto pela API. A migration security_invoker_views_publicas
--    move a lógica privilegiada para private.view_* e mantém em public apenas
--    wrappers security_invoker=true. Se este arquivo for reaplicado, rode
--    aquela migration em seguida.
-- ----------------------------------------------------------------------------

-- Comentários de questão: o feed é público por desenho (a rota Flask
-- /api/comentarios/<id> não exige login). A view NÃO expõe id_usuario.
drop view if exists public.view_comentarios_publicos;
create view public.view_comentarios_publicos
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

revoke all on public.view_comentarios_publicos from anon, authenticated;
grant select on public.view_comentarios_publicos to anon, authenticated;
comment on view public.view_comentarios_publicos is
    'F-01: feed público de comentários sem id_usuario/auth_id. SELECT para anon/authenticated.';

-- Simulados públicos: somente eh_privado = false. Expõe o username do
-- criador (nome de exibição público), nunca id_criador/e-mail. `eh_meu`
-- permite à UI mostrar o botão de excluir sem revelar o id do dono.
drop view if exists public.view_simulados_publicos;
create view public.view_simulados_publicos
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

revoke all on public.view_simulados_publicos from anon, authenticated;
grant select on public.view_simulados_publicos to authenticated;
comment on view public.view_simulados_publicos is
    'F-01: simulados públicos (eh_privado=false) sem id_criador/e-mail. SELECT apenas authenticated.';

-- Questões dos simulados públicos: necessário para o aluno fazer a prova.
-- Não expõe nada além de (id_simulado, id_questao), que já são públicos.
drop view if exists public.view_simulados_questoes_publicas;
create view public.view_simulados_questoes_publicas
with (security_barrier = true, security_invoker = false)
as
select
    sq.id_simulado,
    sq.id_questao
from public.simulados_questoes sq
join public.simulados s on s.id = sq.id_simulado
where s.eh_privado is false;

revoke all on public.view_simulados_questoes_publicas from anon, authenticated;
grant select on public.view_simulados_questoes_publicas to authenticated;
comment on view public.view_simulados_questoes_publicas is
    'F-01: questões de simulados públicos. SELECT apenas authenticated.';

-- Ranking: função SECURITY DEFINER com search_path vazio e checagem de
-- auth.uid(). Libera ranking de simulado público para qualquer autenticado e
-- ranking de simulado privado apenas para o criador. Devolve somente o
-- username (nome de exibição) e as métricas do ranking — nunca id_usuario.
--
-- ATENÇÃO (lint 0029): este desenho original mantinha a função SECURITY
-- DEFINER no schema exposto. A migration ranking_simulado_private_wrapper move
-- a lógica para private.ranking_simulado e deixa em public apenas um wrapper
-- SECURITY INVOKER. Se este arquivo for reaplicado, rode aquela migration em
-- seguida.
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

revoke all on function public.ranking_simulado(uuid) from public, anon;
grant execute on function public.ranking_simulado(uuid) to authenticated;
comment on function public.ranking_simulado(uuid) is
    'F-01/F-05: ranking de simulado público para authenticated; privado apenas para o criador.';
