-- ============================================================================
-- F-03 — Vínculo de questão só no próprio caderno
--
-- A rota /api/cadernos/salvar recebe id_caderno do cliente e passa a validar
-- a posse antes do INSERT. Esta migration coloca a mesma regra no banco, de
-- forma declarativa:
--   * caderno_questoes.id_usuario passa a ser NOT NULL;
--   * índice único (id_caderno, id_usuario) em cadernos;
--   * FK composta (id_caderno, id_usuario)
--       -> cadernos (id_caderno, id_usuario)
--     ON UPDATE CASCADE / ON DELETE CASCADE.
--
-- Resultado: nem o app, nem um cliente com JWT + x-app-token, nem o painel
-- administrativo (service_role) conseguem inserir/alterar um vínculo cujo
-- id_usuario diverga do dono do caderno. A FK substitui a antiga FK simples
-- de id_caderno (o vínculo com o caderno continua garantido, agora junto do
-- dono).
--
-- IDEMPOTENTE: pode ser reaplicada. Aplicar via MCP (apply_migration) ou SQL
-- Editor. Teste transacional: docs/migrations/test_f03.sql.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 0. Falha cedo se já houver dados inconsistentes. Não apaga nem reescreve
--    dados de aluno: a correção deve ser uma decisão explícita do operador.
--    (Produção em 2026-11-03: 0 cadernos e 0 vínculos, então é no-op.)
-- ----------------------------------------------------------------------------
do $$
begin
    if exists (select 1 from public.caderno_questoes where id_usuario is null) then
        raise exception
            'F-03: existem linhas em caderno_questoes com id_usuario NULL; corrija antes de aplicar';
    end if;

    if exists (
        select 1
        from public.caderno_questoes cq
        join public.cadernos c on c.id_caderno = cq.id_caderno
        where cq.id_usuario <> c.id_usuario
    ) then
        raise exception
            'F-03: existem vínculos cross-tenant em caderno_questoes; corrija antes de aplicar';
    end if;
end $$;

-- ----------------------------------------------------------------------------
-- 1. O dono do vínculo é obrigatório.
-- ----------------------------------------------------------------------------
alter table public.caderno_questoes
    alter column id_usuario set not null;

-- ----------------------------------------------------------------------------
-- 2. Colunas referenciadas pela FK composta precisam ser únicas.
--    (id_caderno já é PK; o par é único por consequência, mas o índice é
--    exigido pelo Postgres como alvo da FK.)
-- ----------------------------------------------------------------------------
create unique index if not exists cadernos_id_caderno_id_usuario_uidx
    on public.cadernos (id_caderno, id_usuario);

-- ----------------------------------------------------------------------------
-- 3. Troca a FK simples por uma composta que amarra dono do vínculo e dono do
--    caderno. Recriada do zero para manter a migration idempotente.
-- ----------------------------------------------------------------------------
alter table public.caderno_questoes
    drop constraint if exists caderno_questoes_id_caderno_fkey;
alter table public.caderno_questoes
    drop constraint if exists caderno_questoes_caderno_dono_fkey;
alter table public.caderno_questoes
    add constraint caderno_questoes_caderno_dono_fkey
    foreign key (id_caderno, id_usuario)
    references public.cadernos (id_caderno, id_usuario)
    on update cascade
    on delete cascade;

comment on constraint caderno_questoes_caderno_dono_fkey
    on public.caderno_questoes is
    'F-03: id_usuario do vínculo deve ser o dono do caderno referenciado.';

-- ----------------------------------------------------------------------------
-- 4. Defesa em profundidade na RLS: INSERT/UPDATE de caderno_questoes também
--    exige que o caderno pertença ao mesmo aluno. A subconsulta em cadernos
--    passa pela policy owner-only, então só enxerga o caderno do próprio dono.
--    Sem isso, a FK sozinha ainda permitiria um INSERT com id_usuario spoofado
--    (o app sempre usa current_user.id, mas a policy fecha a porta no banco).
-- ----------------------------------------------------------------------------
drop policy if exists anon_escreve_dados_aluno on public.caderno_questoes;
create policy anon_escreve_dados_aluno on public.caderno_questoes
    for insert to anon, authenticated
    with check (
        public.eh_app_aluno()
        and public.eh_dono_do_aluno(id_usuario)
        and exists (
            select 1
            from public.cadernos c
            where c.id_caderno = caderno_questoes.id_caderno
              and c.id_usuario = caderno_questoes.id_usuario
        )
    );

drop policy if exists anon_atualiza_dados_aluno on public.caderno_questoes;
create policy anon_atualiza_dados_aluno on public.caderno_questoes
    for update to anon, authenticated
    using (
        public.eh_app_aluno()
        and public.eh_dono_do_aluno(id_usuario)
    )
    with check (
        public.eh_app_aluno()
        and public.eh_dono_do_aluno(id_usuario)
        and exists (
            select 1
            from public.cadernos c
            where c.id_caderno = caderno_questoes.id_caderno
              and c.id_usuario = caderno_questoes.id_usuario
        )
    );
