-- ============================================================================
-- F-04 — Resultado de simulado só em simulado público ou do próprio aluno
--
-- A rota /aluno/simulados/corrigir/<id> já usa o guard único
-- _simulado_do_usuario_ou_none (fazer/corrigir/ranking/PDF): simulado privado
-- de outro aluno devolve a mesma resposta de "não encontrado" antes de
-- consultar questões, gabarito, resultados ou a RPC de ranking.
--
-- Esta migration coloca a mesma regra no banco. As policies de INSERT/UPDATE
-- de simulados_resultados validavam apenas o dono do RESULTADO
-- (eh_dono_do_aluno(id_usuario)); com JWT + x-app-token, um aluno conseguia
-- inserir um resultado falso em simulado privado alheio via PostgREST. Agora
-- o id_simulado precisa ser:
--   * público (view_simulados_publicos, que só expõe eh_privado=false), ou
--   * do próprio aluno (tabela simulados sob RLS owner-only).
--
-- A view é security definer (security_invoker=false) e devolve apenas as
-- colunas públicas; a subconsulta em simulados enxerga somente as linhas do
-- próprio aluno por causa da policy owner-only. Nenhuma função nova é criada.
--
-- IDEMPOTENTE: pode ser reaplicada. Aplicar via MCP (apply_migration) ou SQL
-- Editor. Teste transacional: docs/migrations/test_f04.sql.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 0. Falha cedo se já houver resultado em simulado privado de outro aluno.
--    Não apaga nem reescreve dados de aluno: a correção (remover resultado
--    fraudulento ou reatribuir) é uma decisão explícita do operador.
--    (Produção em 2026-11-03: 0 resultados, então é no-op.)
-- ----------------------------------------------------------------------------
do $$
begin
    if exists (
        select 1
        from public.simulados_resultados r
        join public.simulados s on s.id = r.id_simulado
        where s.eh_privado is true
          and s.id_criador is distinct from r.id_usuario
    ) then
        raise exception
            'F-04: existem resultados em simulados privados de outro aluno; corrija antes de aplicar';
    end if;
end $$;

-- ----------------------------------------------------------------------------
-- 1. INSERT: dono do resultado + simulado público OU do próprio aluno.
-- ----------------------------------------------------------------------------
drop policy if exists anon_escreve_dados_aluno on public.simulados_resultados;
create policy anon_escreve_dados_aluno on public.simulados_resultados
    for insert to anon, authenticated
    with check (
        public.eh_app_aluno()
        and public.eh_dono_do_aluno(id_usuario)
        and (
            exists (
                select 1
                from public.view_simulados_publicos v
                where v.id = simulados_resultados.id_simulado
            )
            or exists (
                select 1
                from public.simulados s
                where s.id = simulados_resultados.id_simulado
                  and public.eh_dono_do_aluno(s.id_criador)
            )
        )
    );

-- ----------------------------------------------------------------------------
-- 2. UPDATE: a linha atual e a nova precisam continuar no mesmo contrato.
--    O USING impede mover/alterar um resultado que aponte para simulado
--    privado alheio; o WITH CHECK impede redirecionar o resultado para um.
-- ----------------------------------------------------------------------------
drop policy if exists anon_atualiza_dados_aluno on public.simulados_resultados;
create policy anon_atualiza_dados_aluno on public.simulados_resultados
    for update to anon, authenticated
    using (
        public.eh_app_aluno()
        and public.eh_dono_do_aluno(id_usuario)
        and (
            exists (
                select 1
                from public.view_simulados_publicos v
                where v.id = simulados_resultados.id_simulado
            )
            or exists (
                select 1
                from public.simulados s
                where s.id = simulados_resultados.id_simulado
                  and public.eh_dono_do_aluno(s.id_criador)
            )
        )
    )
    with check (
        public.eh_app_aluno()
        and public.eh_dono_do_aluno(id_usuario)
        and (
            exists (
                select 1
                from public.view_simulados_publicos v
                where v.id = simulados_resultados.id_simulado
            )
            or exists (
                select 1
                from public.simulados s
                where s.id = simulados_resultados.id_simulado
                  and public.eh_dono_do_aluno(s.id_criador)
            )
        )
    );
