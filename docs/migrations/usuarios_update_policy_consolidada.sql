-- ============================================================================
-- Lint 0006 — Multiple Permissive Policies no UPDATE de usuarios
--
-- Havia duas policies permissivas de UPDATE em public.usuarios para o papel
-- `authenticated`:
--   * anon_atualiza_dados_aluno — dono do perfil (auth.uid() = auth_id);
--   * relink_perfil_legado — adoção de linha legada (auth_id IS NULL) cujo
--     e-mail confirmado do JWT bate com o e-mail da linha.
--
-- O PostgreSQL avalia TODAS as policies permissivas aplicáveis; para o mesmo
-- papel/ação isso é redundante e custa performance em cada UPDATE. As duas
-- têm o mesmo WITH CHECK (o resultado precisa ficar com auth.uid() = auth_id),
-- então basta uma policy com o USING em OR.
--
-- Segurança preservada:
--   * o UPDATE continua exigindo o header x-app-token (eh_app_aluno());
--   * só o próprio perfil ou uma linha legada de MESMO e-mail confirmado é
--     visível para atualização;
--   * o resultado do UPDATE continua obrigatoriamente vinculado ao auth.uid(),
--     então ninguém adota a linha para outro usuário nem troca o auth_id para
--     terceiros;
--   * anon permanece sem grant de UPDATE (a policy não amplia privilégio).
--
-- IDEMPOTENTE: pode ser reaplicada. Aplicar via MCP (apply_migration) ou SQL
-- Editor. Teste transacional: docs/migrations/test_usuarios_update_consolidada.sql.
-- ============================================================================

drop policy if exists anon_atualiza_dados_aluno on public.usuarios;
drop policy if exists relink_perfil_legado on public.usuarios;
drop policy if exists usuarios_update_proprio_ou_relink on public.usuarios;

create policy usuarios_update_proprio_ou_relink on public.usuarios
for update
to anon, authenticated
using (
    eh_app_aluno()
    and (
        (select auth.uid()) = auth_id
        or (
            auth_id is null
            and lower(email) = lower(((select auth.jwt()) ->> 'email'))
        )
    )
)
with check (
    eh_app_aluno()
    and (select auth.uid()) = auth_id
);

comment on policy usuarios_update_proprio_ou_relink on public.usuarios is
    'Lint 0006: policy única de UPDATE (próprio perfil ou adoção de linha legada sem auth_id de mesmo e-mail). Substitui anon_atualiza_dados_aluno + relink_perfil_legado.';
