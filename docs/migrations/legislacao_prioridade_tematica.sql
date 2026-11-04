-- RAG leve de legislação — prioridade estrita da taxonomia
-- Corrige `buscar_legislacao`: aplica o melhor escopo disponível (tópico >
-- matéria > FTS global), em vez de misturar resultados de tópico e matéria.

create or replace function public.buscar_legislacao(
    p_texto text,
    p_id_subtopico bigint default null,
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
    with bruto as (
        select left(coalesce(p_texto, ''), 2000) as txt
    ),
    tsq as (
        select case
            when nullif(trim(bruto.txt), '') is null then null
            else plainto_tsquery('portuguese', bruto.txt)
        end as q_and
        from bruto
    ),
    qor as (
        select case
            when tsq.q_and is null or tsq.q_and = ''::tsquery then null
            else to_tsquery('portuguese', replace(tsq.q_and::text, ' & ', ' | '))
        end as q_or
        from tsq
    ),
    candidatos as (
        select l.id,
               l.referencia,
               l.texto,
               l.vigencia_de,
               l.vigencia_ate,
               case
                   when l.id_topico is not null
                        and l.id_topico = coalesce(p_id_topico,
                            (select s.id_topico from public.subtopicos s where s.id_subtopico = p_id_subtopico)) then 4
                   when l.id_materia is not null
                        and l.id_materia = coalesce(p_id_materia,
                            (select s.id_materia from public.subtopicos s where s.id_subtopico = p_id_subtopico)) then 2
                   else 0
               end as pont_estrutura,
               case
                   when tsq.q_and is not null and l.search_tsv @@ tsq.q_and then 2
                   else 1
               end as forca,
               case
                   when tsq.q_and is null then 0::real
                   else coalesce(ts_rank_cd(l.search_tsv,
                          case when l.search_tsv @@ tsq.q_and then tsq.q_and else qor.q_or end), 0)::real
               end as rk
        from public.legislacao_artigos l
        cross join tsq
        cross join qor
        where tsq.q_and is null
           or l.search_tsv @@ tsq.q_and
           or l.search_tsv @@ qor.q_or
    ),
    melhor_escopo as (
        select max(pont_estrutura) as pont_estrutura
        from candidatos
    )
    select c.id, c.referencia, c.texto, c.vigencia_de, c.vigencia_ate,
           (c.pont_estrutura + c.forca + c.rk)::real as relevancia
    from candidatos c
    cross join melhor_escopo e
    where c.pont_estrutura = e.pont_estrutura
    order by c.pont_estrutura desc, c.forca desc, c.rk desc, c.id
    limit least(greatest(coalesce(p_limite, 5), 1), 10)
$$;
