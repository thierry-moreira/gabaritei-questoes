-- =============================================================================
-- RAG leve de legislação — contexto para /api/ia_explica
-- Migration: legislacao_busca
--
-- Aplicar no Supabase (editor SQL / pipeline do painel administrativo).
-- STATUS: aplicada em 2026-11-01 no projeto Supabase (ref ivhuaevrrkrnagbqmnwc),
-- via MCP (`apply_migration` nomeada `legislacao_busca`) — inclui o fix
-- `set search_path = ''` na função (advisor function_search_path_mutable).
-- O app do aluno apenas CONSULTA (anon + RLS de leitura); a ingestão do
-- corpus é exclusiva do painel (service_role, fora deste repo).
--
-- O que esta migration faz:
--   1. Tabela `legislacao_artigos` — corpus curado de dispositivos legais
--      (referência, texto fiel, vigência e tags da taxonomia).
--   2. Busca lexical (FTS português) + filtro estruturado por matéria/tópico
--      via RPC `buscar_legislacao` — sem embeddings/vetores: legislação é
--      altamente lexical e a camada BYOK não tem embeddings compatíveis
--      entre provedores.
--   3. Coluna `explicacoes_ia.contexto_legislacao` (jsonb) — evidência dos
--      trechos usados na geração, para auditoria/revalidação do cache.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1) Corpus curado (ingestão: painel admin com service_role)
-- -----------------------------------------------------------------------------
create table if not exists public.legislacao_artigos (
    id           bigint generated always as identity primary key,
    referencia   text not null unique,       -- ex.: 'Lei nº 8.112/1990 — art. 117, inciso IX'
    texto        text not null,              -- transcrição fiel do dispositivo
    vigencia_de  date,                       -- início da vigência desta redação
    vigencia_ate date,                       -- fim (null = redação vigente)
    id_materia   bigint references public.materias (id_materia) on delete set null,
    id_topico    bigint references public.topicos (id_topico) on delete set null,
    criado_em    timestamptz not null default now(),
    constraint legislacao_vigencia_coerente
        check (vigencia_ate is null or vigencia_de is null or vigencia_ate >= vigencia_de)
);

-- Índice de busca lexical: referência pesa mais (peso A) que o texto (B).
alter table public.legislacao_artigos
    add column if not exists search_tsv tsvector
    generated always as (
        setweight(to_tsvector('portuguese', coalesce(referencia, '')), 'A') ||
        setweight(to_tsvector('portuguese', coalesce(texto, '')), 'B')
    ) stored;

create index if not exists idx_legislacao_search
    on public.legislacao_artigos using gin (search_tsv);
create index if not exists idx_legislacao_taxonomia
    on public.legislacao_artigos (id_materia, id_topico);

-- Leitura pública (conteúdo é aberto por design, como as demais tabelas de
-- conteúdo); escrita exclusiva do painel (service_role bypassa RLS).
alter table public.legislacao_artigos enable row level security;
drop policy if exists "anon_le_legislacao" on public.legislacao_artigos;
create policy "anon_le_legislacao" on public.legislacao_artigos
    for select to anon, authenticated using (true);
grant select on public.legislacao_artigos to anon, authenticated;
revoke insert, update, delete, truncate on public.legislacao_artigos from anon, authenticated;

-- -----------------------------------------------------------------------------
-- 2) RPC de retrieval: FTS + preferência por tópico > matéria > texto puro
-- -----------------------------------------------------------------------------
create or replace function public.buscar_legislacao(
    p_texto text,
    p_id_materia bigint default null,
    p_id_topico bigint default null,
    p_limite int default 5
)
returns table (
    id bigint,
    referencia text,
    texto text,
    vigencia_de date,
    vigencia_ate date,
    relevancia real
)
language sql
stable
set search_path = ''
as $$
    with tsq as (
        select case
            when nullif(trim(coalesce(p_texto, '')), '') is null then null
            else plainto_tsquery('portuguese', left(coalesce(p_texto, ''), 2000))
        end as q
    ),
    candidatos as (
        select l.id,
               l.referencia,
               l.texto,
               l.vigencia_de,
               l.vigencia_ate,
               case
                   when p_id_topico is not null and l.id_topico = p_id_topico then 4
                   when p_id_materia is not null and l.id_materia = p_id_materia then 2
                   else 0
               end as pont_estrutura,
               case
                   when tsq.q is null then 0::real
                   else coalesce(ts_rank_cd(l.search_tsv, tsq.q), 0)::real
               end as rk
        from public.legislacao_artigos l
        cross join tsq
        where tsq.q is null or l.search_tsv @@ tsq.q
    )
    -- Precisão primeiro: se há qualquer acerto na taxonomia da questão,
    -- descarta acertos "genéricos" fora dela; senão, cai para o FTS puro.
    select c.id, c.referencia, c.texto, c.vigencia_de, c.vigencia_ate,
           (c.pont_estrutura + c.rk)::real as relevancia
    from candidatos c
    where c.pont_estrutura > 0
       or not exists (select 1 from candidatos c2 where c2.pont_estrutura > 0)
    order by c.pont_estrutura desc, c.rk desc, c.id
    limit least(greatest(coalesce(p_limite, 5), 1), 10)
$$;

grant execute on function public.buscar_legislacao(text, bigint, bigint, int) to anon, authenticated;
revoke execute on function public.buscar_legislacao(text, bigint, bigint, int) from public;

-- -----------------------------------------------------------------------------
-- 3) Evidência do RAG no cache global de explicações (auditoria)
--    Linhas antigas ficam com NULL = geradas sem contexto legislativo.
--    Para regerar uma explicação antiga com o RAG, o painel apaga a linha
--    de `explicacoes_ia` e o próximo aluno com chave gera de novo.
-- -----------------------------------------------------------------------------
alter table public.explicacoes_ia
    add column if not exists contexto_legislacao jsonb;
