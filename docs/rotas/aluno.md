# Documentação Técnica: `rotas/aluno.py` (Painel e Estatísticas do Aluno)

## Descrição Geral
O blueprint `aluno` é a porta de entrada do app e o centro das estatísticas de estudo. Ele redireciona a raiz para o login/área do aluno, serve a página de tutoriais, monta o dashboard principal (`/aluno/painel`) e o raio-X detalhado (`/aluno/dashboard_detalhado`), além de persistir a meta diária via API.

Todos os cálculos de data usam o fuso oficial de **Brasília (UTC-3)**, independentemente do fuso da máquina — o mesmo critério do motor de ofensiva em `rotas/questao.py` e de `utils.calcular_ofensiva_usuario`.

---

## Detalhamento das Rotas

### 1. Portão de Entrada (`/`)
*   **Método**: `GET`
*   **Segurança**: pública, com `@limiter.exempt`.
*   **Comportamento**:
    *   visitante → `redirect` para `/aluno/login`;
    *   aluno autenticado → `redirect` para `/aluno/questoes`;
    *   sessão com role diferente de `aluno` → `logout_user()` + flash "A área administrativa roda em aplicativo dedicado (app_admin.py)." e volta ao login.

> [!NOTE]
> A antiga landing de apresentação foi aposentada com o fim do modelo pago; a raiz é apenas o portão do app desktop.

---

### 2. Tutoriais (`/aluno/tutoriais`)
*   **Método**: `GET`
*   **Segurança**: `@aluno_required`
*   **Descrição**: renderiza `aluno/tutoriais.html` com o conteúdo de onboarding do aluno.

---

### 3. Dashboard Principal (`/aluno/painel`)
*   **Método**: `GET`
*   **Segurança**: `@aluno_required` + `@limiter.exempt`
*   **Consultas**:
    1.  total de respostas do aluno (`historico_respostas`, `count=exact`);
    2.  total de acertos (`is_correct = true`);
    3.  histórico com `criado_em` + `is_correct` (limite de 50.000 linhas) para gráfico e ofensiva.
*   **Métricas calculadas**:
    *   **Taxa de acerto**: `round(acertos / total * 100)`, ou `0` sem histórico;
    *   **Ofensiva (streak)**: datas únicas convertidas para UTC-3; se a data mais recente for hoje ou ontem, conta dias consecutivos para trás;
    *   **Gráfico de 30 dias**: acertos e erros por dia (`dd/mm`) no fuso de Brasília;
    *   **Hoje**: questões resolvidas na data atual de Brasília;
    *   **Evolução semanal**: compara os últimos 7 dias com os 7 anteriores; sem semana anterior, usa `semana_atual * 100`;
    *   **Nível de performance**: `Alto Desempenho` (≥80%), `Bom Desempenho` (≥60%), `Desempenho Regular` (≥40%) ou `Precisa de Foco`.
*   **Resiliência**: qualquer exceção no bloco é logada no terminal e o template é renderizado com zeros (`total_resolvidas=0`, `taxa_acerto=0`, listas vazias), exibindo flash de instabilidade em vez de erro 500.

---

### 4. Meta Diária (`/aluno/api/set-meta`)
*   **Método**: `POST` (JSON: `{"meta": <int>}`)
*   **Segurança**: `@aluno_required` + CSRF global.
*   **Validações**: corpo ausente ou `meta` ausente → `400` com `{"error": ...}`.
*   **Persistência**: `usuarios.update({"meta_diaria": int(meta)}).eq("id", str(current_user.id))` via `safe_execute`.
*   **Resposta**: `{"success": true}` (`200`) ou `{"error": "Erro ao salvar meta diária."}` (`500`).

---

### 5. Dashboard Detalhado / Raio-X (`/aluno/dashboard_detalhado`)
*   **Método**: `GET`
*   **Segurança**: `@aluno_required` + `@limiter.exempt`
*   **Fluxo**:
    1.  Busca todo o histórico do aluno (`id_questao`, `is_correct`, `criado_em`), ordenado do mais recente para o mais antigo;
    2.  Sem histórico → flash "Resolva algumas questões primeiro para gerar seu dashboard!" e redirect para `/aluno/painel`;
    3.  Busca metadados das questões em blocos de 500 ids (`view_questoes_completa`: matéria e tópico);
    4.  Agrega desempenho por matéria e por tópico (acertos, total, taxa e última resolução);
    5.  Monta a evolução de 30 dias por matéria e o calendário de metas do mês atual.
*   **Curva de esquecimento** (dias desde a última resolução da matéria):
    *   `>= 4` dias → **REVISAR** (warning);
    *   `>= 8` dias → **ALERTA**;
    *   `>= 15` dias → **CRÍTICO** (danger).
*   **Pontos de atenção**: tópicos com **≥5 questões** respondidas e **taxa < 60%**, ordenados por taxa e volume (máximo de 10).
*   **Melhor matéria**: exige **≥5 questões** respondidas **e** taxa **≥60%**; entre as elegíveis, vence a maior taxa (desempate pelo volume). Sem matéria elegível, o card não é exibido.
*   **Gráficos**: até 12 matérias no gráfico multi-linha de 30 dias, com paleta fixa de cores.
*   **Template**: `aluno/estatisticas.html`, com `meta_diaria`, `concluidos_por_dia` e os top 5 alertas de revisão.

---

## Segurança e Privacidade

*   Todas as consultas a dados do aluno filtram por `current_user.id`; o aluno nunca lê o histórico de outro pela rota. As consultas à `view_questoes_completa` buscam apenas metadados públicos das questões.
*   As páginas de dashboard são `@limiter.exempt` para não punir navegação legítima; a API de meta continua sob o rate limit global.
*   Nenhum ID de questão/matéria vindo da URL é usado para escrita — o dashboard é somente leitura, exceto pela meta diária, que sempre grava no usuário autenticado.

---

## Validação e Testes

A cobertura está em `tests/test_aluno_questoes.py`:

*   `/aluno/painel` com ofensiva em Brasília, agregação por data e taxas de acerto;
*   `/aluno/dashboard_detalhado` com histórico vazio (redirect) e com dados (melhor matéria, pontos de atenção);
*   `/aluno/questoes` com filtro de status padrão `todas` e `nao_respondidas` explícito;
*   resolução de questões e streak via `/aluno/responder` e `/api/responder`.

```powershell
venv\Scripts\python.exe -m unittest tests.test_aluno_questoes -v
```
