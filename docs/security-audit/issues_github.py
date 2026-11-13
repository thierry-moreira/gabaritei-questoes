# -*- coding: utf-8 -*-
"""Textos completos das issues para o GitHub.

Cada item vira um bloco Markdown no fim do PDF, delimitado por
``--- ISSUE n ---`` e ``--- FIM ISSUE n ---``. O texto foi escrito para
copiar e colar diretamente no GitHub, com evidência, impacto, correção e
critérios de aceite verificáveis.
"""

from __future__ import annotations

ISSUES: list[dict[str, str]] = [
    {
        "title": "[Segurança] RLS de SELECT aberta expõe dados de todos os alunos",
        "labels": "security, severity:critical, database, rls",
        "body": """# [Segurança] RLS de SELECT aberta expõe dados de todos os alunos

**Labels sugeridas:** `security`, `severity:critical`, `database`, `rls`

## Descrição do problema

A documentação do projeto declara que as tabelas de dados do aluno têm
`SELECT` livre para o papel `anon`, com exceção apenas das três tabelas de
progresso de edital. A anon key é pública e está embutida no cliente
(`desktop/main.js` e `site/index.html`). Com essa chave, qualquer pessoa
consegue consultar o PostgREST e ler dados de todos os alunos, sem login.

Tabelas citadas na documentação: `usuarios`, `historico_respostas`,
`comentarios_questao`, `flashcards`, `flashcard_categorias`,
`resumos_estudo`, `cadernos`, `caderno_questoes`, `filtros_salvos`,
`simulados`, `simulados_questoes`, `simulados_resultados` e `editais_*`.

## Evidência

- `docs/banco_dados.md:27` — "Dados do aluno (16 tabelas...): SELECT livre".
- `docs/banco_dados.md:38` — "a leitura dos dados de estudo é liberada pelo
  desenho atual (privacidade entre alunos não é garantida em SELECT, com
  exceção das 3 tabelas de edital)".
- `desktop/main.js:26-27` — URL e anon key hardcoded.
- `site/index.html:194-195` — URL e anon key hardcoded.

```http
GET https://<projeto>.supabase.co/rest/v1/usuarios?select=*
apikey: <SUPABASE_ANON_KEY>
```

## Por que é explorável

A policy de SELECT para `anon` é o único controle. A chave é pública por
design, então não há barreira de autenticação. O atacante não precisa de
conta nem de engenharia social: basta extrair a chave do bundle ou do site
e chamar a API REST.

> Observação: não foi executada consulta contra a produção. A exploração
> depende de a configuração documentada estar vigente no projeto Supabase.

## Impacto

- Leitura de e-mail/nome de usuário, histórico de respostas, comentários,
  flashcards, resumos, cadernos, filtros, simulados e resultados.
- Correlação entre alunos e reconstrução de rotina de estudos.
- Base para phishing e para os IDORs descritos em outras issues.

## Sugestão de correção

1. Recriar as policies de SELECT das tabelas de aluno como owner-only:
   `auth.uid() = id_usuario` (ou `auth_id` em `usuarios`).
2. Manter conteúdo público (questões, alternativas, taxonomia) em tabelas
   separadas ou views públicas, sem misturar com dados de aluno.
3. Validar com dois usuários reais e com a anon key sem JWT.
4. Versionar as migrations de RLS neste repositório.

## Critérios de aceite

- [ ] A anon key sozinha retorna 0 linhas de `usuarios`,
      `historico_respostas`, `comentarios_questao`, `flashcards`,
      `cadernos`, `filtros_salvos` e `simulados`.
- [ ] O usuário B não lê nenhuma linha do usuário A em todas as tabelas
      de dados de aluno.
- [ ] Questões e taxonomia públicas continuam acessíveis.
- [ ] Migrations de RLS estão versionadas e há teste de regressão.
""",
    },
    {
        "title": "[Segurança] IDOR em cadernos: leitura e escrita em cadernos de outros alunos",
        "labels": "security, severity:high, backend, idor",
        "body": """# [Segurança] IDOR em cadernos: leitura e escrita em cadernos de outros alunos

**Labels sugeridas:** `security`, `severity:high`, `backend`, `idor`

## Descrição do problema

Duas rotas de cadernos confiam no `id_caderno` recebido e não verificam se
o caderno pertence ao usuário autenticado:

1. `visualizar_caderno` lê o nome e as questões apenas por `id_caderno`.
2. `salvar_na_pasta` insere uma questão em qualquer `id_caderno`, usando o
   `id_usuario` do atacante. A vítima vê a questão porque a leitura também
   é feita só por `id_caderno`; e não consegue removê-la porque a remoção
   filtra pelo `id_usuario` do chamador.

## Evidência

```python
# rotas/caderno.py:33-37
query_nome = supabase.table("cadernos").select("nome_caderno")\\
    .eq("id_caderno", id_caderno).single()
query_ids = supabase.table("caderno_questoes")\\
    .select("id_questao").eq("id_caderno", id_caderno)
```

```python
# rotas/caderno.py:119-123
supabase.table("caderno_questoes").insert({
    "id_caderno": id_caderno,
    "id_questao": id_questao,
    "id_usuario": current_user.id
})
```

```python
# rotas/caderno.py:168-174 (remoção)
query_delete = (
    supabase.table("caderno_questoes").delete()
    .eq("id_caderno", id_caderno)
    .eq("id_questao", id_questao_int)
    .eq("id_usuario", user_id)
)
```

## Por que é explorável

O `id_caderno` é numérico e sequencial. Qualquer aluno autenticado pode
enumerar `/aluno/caderno/1`, `/aluno/caderno/2` etc. e ler o conteúdo; com
um POST em `/api/cadernos/salvar`, pode inserir questões no caderno de
outra pessoa. O RLS de escrita permite o insert porque o `id_usuario`
gravado é o do atacante, não o da vítima.

## Impacto

- Leitura de conteúdo de estudo alheio.
- Poluição persistente de cadernos de terceiros.
- A vítima não consegue remover a questão inserida pelo atacante.

## Sugestão de correção

1. Em `visualizar_caderno`, adicionar `.eq("id_usuario", current_user.id)`
   nas consultas de `cadernos` e `caderno_questoes`; devolver 404 se não
   encontrar.
2. Em `salvar_na_pasta`, buscar o caderno com
   `.eq("id_caderno", id_caderno).eq("id_usuario", current_user.id)` antes
   do insert; rejeitar se não existir.
3. Reforçar no banco: FK/constraint ou policy que amarre
   `caderno_questoes.id_usuario` ao dono de `cadernos.id_usuario`.
4. Adicionar teste com dois usuários.

## Critérios de aceite

- [ ] O usuário B recebe 404/403 ao abrir o caderno do usuário A.
- [ ] O usuário B não consegue inserir questão no caderno do usuário A.
- [ ] O usuário A consegue remover qualquer questão do próprio caderno.
- [ ] Teste de regressão cobre leitura e escrita cross-tenant.
""",
    },
    {
        "title": "[Segurança] Simulados privados acessíveis por ID em correção, ranking e PDF",
        "labels": "security, severity:high, backend, idor, simulados",
        "body": """# [Segurança] Simulados privados acessíveis por ID em correção, ranking e PDF

**Labels sugeridas:** `security`, `severity:high`, `backend`, `idor`, `simulados`

## Descrição do problema

A rota `fazer_simulado` bloqueia simulado privado de outro usuário, mas o
mesmo guard não foi replicado em três rotas que também aceitam
`id_simulado`:

- `corrigir_simulado`: calcula e devolve o gabarito; também insere um
  resultado para o atacante.
- `ver_ranking_simulado`: lista participantes e notas.
- `baixar_pdf_simulado`: monta a prova e inclui `letra_gabarito`.

Qualquer aluno autenticado com o ID (numérico e sequencial) acessa o
conteúdo de um simulado privado alheio.

## Evidência

```python
# rotas/simulado.py:145-147 — guard correto, só em fazer_simulado
if simulado.get('eh_privado') and simulado.get('id_criador') != current_user.id:
    flash("Você não tem permissão para acessar este simulado.", "danger")
    return redirect('/aluno/simulados')
```

```python
# rotas/simulado.py:188-220 — corrigir sem guard
res_simulado = safe_execute(
    supabase.table('simulados').select('*').eq('id', id_simulado).single())
...
detalhes_resultado.append({
    'id_questao': q_id,
    'resposta_aluno': resposta_aluno,
    'resposta_correta': correta,
    'correto': eh_correto
})
```

```python
# rotas/simulado.py:280-296 — ranking sem guard
res_simulado = safe_execute(
    supabase.table('simulados').select('titulo, eh_privado')
    .eq('id', id_simulado).single())
...
res_ranking = safe_execute(
    supabase.table('simulados_resultados')
    .select('nota, respostas_corretas, total_questoes, data_conclusao, usuarios(username)')
    .eq('id_simulado', id_simulado)
    .order('nota', desc=True).limit(50))
```

```python
# rotas/simulado.py:312-360 — PDF sem guard e com gabarito
res_simulado = safe_execute(
    supabase.table('simulados').select('*').eq('id', id_simulado).single())
...
q['letra_gabarito'] = letra_certa if letra_certa else 'N/A'
```

## Por que é explorável

O atacante só precisa estar logado como aluno e conhecer/adivinhar o ID.
Não há verificação de dono nem de privacidade nas três rotas. A correção
ainda grava `simulados_resultados`, permitindo poluir o ranking do simulado
privado da vítima.

## Impacto

- Exposição do gabarito e das questões de simulados privados.
- Exposição de participantes, notas e desempenho.
- Poluição de resultados/ranking.
- Quebra da expectativa de privacidade do recurso.

## Sugestão de correção

1. Criar um helper único, por exemplo
   `_simulado_do_usuario_ou_404(id_simulado)`, que busca o simulado e
   compara `eh_privado`/`id_criador` com `current_user.id`.
2. Chamar o helper no início de `corrigir_simulado`,
   `ver_ranking_simulado` e `baixar_pdf_simulado`, antes de qualquer
   consulta de questões/resultados.
3. Para simulado privado, permitir ranking apenas ao criador ou desabilitar
   a tela.
4. Testar com dois usuários e com simulado público.

## Critérios de aceite

- [ ] Não-dono recebe 403/404 em corrigir, ranking e PDF de simulado privado.
- [ ] Nenhuma questão, alternativa ou gabarito é retornada antes do guard.
- [ ] Criador e simulado público continuam funcionando.
- [ ] Teste de regressão cobre as três rotas.
""",
    },
    {
        "title": "[Segurança] XSS armazenado em comentários permite executar JS na sessão da vítima",
        "labels": "security, severity:high, frontend, backend, xss",
        "body": """# [Segurança] XSS armazenado em comentários permite executar JS na sessão da vítima

**Labels sugeridas:** `security`, `severity:high`, `frontend`, `backend`, `xss`

## Descrição do problema

O backend grava o texto do comentário e o nome de usuário sem sanitização.
O nome vem de `usuarios.username`, que o próprio aluno edita em
`/aluno/conta/`. A listagem pública busca os comentários e o JavaScript
monta o HTML com template literals e `innerHTML`, interpolando o nome e o
texto. Não há DOMPurify, bleach ou nh3 no projeto. O CSP permite
`'unsafe-inline'` em `script-src`, então um payload com `onerror` executa.

O ataque é armazenado: o payload fica no banco e dispara para qualquer
usuário que abra/expanda os comentários da questão, não apenas para quem o
criou.

## Evidência

```python
# rotas/questao.py:348-353
query_insert = supabase.table("comentarios_questao").insert({
    "id_questao": id_questao,
    "id_usuario": str(current_user.id),
    "nome_usuario": nome_aluno,
    "texto_comentario": texto
})
```

```javascript
// static/js/questoes_common.js:229-238
html += `
<div class="mb-2 p-2 bg-white rounded border shadow-sm text-dark">
  <div class="d-flex justify-content-between align-items-center mb-1">
    <strong class="small text-primary">
      <i class="bi bi-person-circle"></i> ${comentario.nome_usuario || 'Aluno'}
    </strong>
    ...
  </div>
  <p class="mb-0 small">${comentario.texto_comentario || comentario.texto || ''}</p>
</div>`;
...
divLista.innerHTML = html;
```

```python
# app.py:146-151
'script-src': [
    '\\'self\\'',
    '\\'unsafe-inline\\'',
    'https://cdn.jsdelivr.net',
    'https://cdn.ckeditor.com',
],
```

```python
# rotas/conta.py:35-44 — username editável e sem escape
novo_username = request.form.get('username')
...
supabase.table("usuarios").update(dados_update).eq("id", current_user.id)
```

Payload mínimo de prova:

```html
<img src=x onerror=alert(document.domain)>
```

## Por que é explorável

`innerHTML` não executa `<script>`, mas executa handlers de evento como
`onerror`. O CSP com `'unsafe-inline'` permite o handler. O backend não
escapa nem valida o conteúdo. O endpoint de comentários é público para
leitura e qualquer aluno autenticado pode publicar.

## Impacto

- Execução de JavaScript no contexto do app, com a sessão da vítima.
- Ações em nome da vítima (responder, criar/editar dados, denunciar).
- Leitura do DOM/CSRF token e exfiltração de dados.
- No Electron, `contextIsolation`/`sandbox` limitam o acesso ao Node, mas
  não impedem requisições same-origin.

## Sugestão de correção

1. Sanitizar a saída com DOMPurify (allowlist) antes de atribuir a
   `innerHTML`; para nome e texto, preferir `textContent`.
2. Sanitizar também no servidor (bleach/nh3) como defesa em profundidade.
3. Remover `'unsafe-inline'` do `script-src` e usar nonces/hashes.
4. Adicionar `object-src 'none'` e `base-uri 'self'` ao CSP.
5. Criar teste de regressão com payloads de XSS.

## Critérios de aceite

- [ ] `<img src=x onerror=alert(1)>` é renderizado como texto, sem executar.
- [ ] O nome de usuário também é tratado como texto.
- [ ] O CSP não contém `'unsafe-inline'` em `script-src`.
- [ ] Teste automatizado cobre comentário e username maliciosos.
""",
    },
    {
        "title": "[Segurança] /api/responder confia no is_correct enviado pelo cliente",
        "labels": "security, severity:medium, backend, integrity",
        "body": """# [Segurança] /api/responder confia no is_correct enviado pelo cliente

**Labels sugeridas:** `security`, `severity:medium`, `backend`, `integrity`

## Descrição do problema

O endpoint `/api/responder` lê `is_correct` do JSON enviado pelo cliente e
grava o valor diretamente em `historico_respostas`. O cliente pode enviar
`true` para qualquer resposta, inflando acertos, ofensiva e estatísticas.
A rota principal `/aluno/responder` calcula a correção no servidor, mas a
rota alternativa permanece. O frontend atual chama apenas
`/aluno/responder`, então a rota parece legada.

## Evidência

```python
# rotas/questao.py:287-301
@questao_bp.route('/api/responder', methods=['POST'])
@aluno_required
@limiter.exempt
def salvar_resposta():
    data = request.json
    id_questao = data.get('id_questao')
    id_alternativa = data.get('id_alternativa')
    is_correct = data.get('is_correct')
    query_historico = supabase.table("historico_respostas").insert({
        "id_usuario": current_user.id,
        "id_questao": id_questao,
        "id_alternativa_marcada": id_alternativa,
        "is_correct": is_correct
    })
```

```python
# rotas/questao.py:33-47 — rota principal, correta
query_alt = supabase.table("alternativas_questao")\\
    .select("id_alternativa, letra, is_correct")\\
    .eq("id_questao", questao_id).order("letra")
...
letra_correta = next((a['letra'] for a in alternativas if a['is_correct']), None)
foi_correta = (letra_escolhida == letra_correta)
```

## Por que é explorável

Basta um POST autenticado com `{"id_questao": 1, "id_alternativa": 2,
"is_correct": true}`. O servidor não consulta o gabarito nem valida a
alternativa; grava o booleano do atacante.

## Impacto

- Histórico e estatísticas de estudo falsificados.
- Ofensiva, dashboard e indicadores derivados incorretos.
- Se algum ranking/relatório usar o histórico, pode ser manipulado.

## Sugestão de correção

1. Ignorar `is_correct` do cliente.
2. Buscar as alternativas da questão no servidor e calcular
   `foi_correta = (letra_escolhida == letra_correta)`.
3. Reutilizar a lógica de `/aluno/responder` ou remover a rota legada se
   não houver chamador.
4. Adicionar teste que envia `is_correct: true` para uma resposta errada.

## Critérios de aceite

- [ ] `is_correct` enviado pelo cliente é ignorado.
- [ ] O servidor calcula a correção a partir do gabarito.
- [ ] Teste prova que um payload forjado não altera o histórico.
- [ ] A rota legada foi removida ou documentada como deprecated.
""",
    },
    {
        "title": "[Segurança] Endpoint público de comentários expõe id_usuario dos alunos",
        "labels": "security, severity:medium, backend, privacy",
        "body": """# [Segurança] Endpoint público de comentários expõe id_usuario dos alunos

**Labels sugeridas:** `security`, `severity:medium`, `backend`, `privacy`

## Descrição do problema

`GET /api/comentarios/<id_questao>` não exige autenticação, usa
`select('*')` e devolve todas as colunas da tabela, incluindo `id_usuario`.
Isso entrega UUIDs de alunos a qualquer visitante e serve de pivô para as
tabelas com SELECT aberto (ver issue crítica de RLS).

## Evidência

```python
# rotas/questao.py:311-320
@questao_bp.route('/api/comentarios/<int:id_questao>', methods=['GET'])
@limiter.exempt
def buscar_comentarios(id_questao):
    query_comentarios = supabase.table("comentarios_questao") \\
        .select("*") \\
        .eq("id_questao", id_questao) \\
        .order("criado_em", desc=True)
    try:
        res = safe_execute(query_comentarios)
        return jsonify(res.data if res.data else [])
```

```python
# rotas/questao.py:348-353 — id_usuario é gravado na tabela
supabase.table("comentarios_questao").insert({
    "id_questao": id_questao,
    "id_usuario": str(current_user.id),
    "nome_usuario": nome_aluno,
    "texto_comentario": texto
})
```

## Por que é explorável

A rota é pública e não há filtro de colunas. Qualquer pessoa pode chamar
`/api/comentarios/1` e receber a lista completa, com UUIDs. Combinado com
`usuarios` de SELECT aberto, o UUID vira nome/e-mail.

## Impacto

- Exposição de identificadores de alunos.
- Facilita correlação com histórico, cadernos e outros dados.
- Aumenta o impacto da falha de RLS.

## Sugestão de correção

1. Selecionar apenas as colunas necessárias:
   `id_comentario, nome_usuario, texto_comentario, criado_em`.
2. Nunca retornar `id_usuario` para o cliente.
3. Paginar/limitar a lista e aplicar rate limit.
4. Se o autor precisar ser identificado para denúncia, usar
   `id_comentario` como referência, não o UUID do usuário.

## Critérios de aceite

- [ ] A resposta não contém `id_usuario`.
- [ ] A rota continua funcionando para leitura pública.
- [ ] Há paginação/limite e teste com anon.
- [ ] Teste verifica que o UUID não aparece no JSON.
""",
    },
    {
        "title": "[Segurança] Checks de posse ausentes em editais e flashcards (defesa em profundidade)",
        "labels": "security, severity:low, backend, idor",
        "body": """# [Segurança] Checks de posse ausentes em editais e flashcards (defesa em profundidade)

**Labels sugeridas:** `security`, `severity:low`, `backend`, `idor`

## Descrição do problema

Duas rotas aceitam IDs de objetos sem validar o dono:

1. `pular_topico_edital` recebe `id_edital` e chama
   `_avancar_ciclo_edital` sem comparar `editais_ciclo.id_usuario` com
   `current_user.id`. Hoje o RLS owner-only das tabelas de progresso
   impede o cross-tenant, mas o código não tem a checagem.
2. `criar_card` aceita `id_categoria` de qualquer usuário. O card é gravado
   com o `id_usuario` do atacante e não aparece na lista da vítima, mas
   cria referência cross-tenant/órfã.

## Evidência

```python
# rotas/edital.py:578-583
@edital_bp.route('/aluno/editais/pular/<int:id_edital>', methods=['POST'])
@aluno_required
def pular_topico_edital(id_edital):
    success, msg, _ = _avancar_ciclo_edital(id_edital, marcar_concluido=True)
```

```python
# rotas/edital.py:157-160 — consulta só por id_edital
res_prog = safe_execute(
    supabase.table("editais_progresso").select("*")
    .eq("id_edital", id_edital).single())
```

```python
# rotas/flashcards.py:118-133
id_cat = dados.get('id_categoria')
...
supabase.table("flashcards").insert({
    "id_usuario": user_id_str,
    "id_categoria": id_cat,
    "frente": frente,
    "verso": verso,
})
```

## Por que é explorável

Hoje o impacto é limitado pelo RLS: `editais_progresso` é owner-only e o
card do atacante não aparece para a vítima. A falha é de defesa em
profundidade: se uma policy for afrouxada ou uma rota for refatorada, o
check de aplicação não existe para segurar.

## Impacto

- Baixo no estado atual.
- Latente: avanço de ciclo de edital alheio se o RLS falhar.
- Poluição referencial de categorias de flashcards.

## Sugestão de correção

1. Em `pular_topico_edital`, validar a posse do edital como em
   `responder_edital` (linhas 485-490) antes de chamar a função.
2. Em `criar_card`, buscar a categoria com
   `.eq("id_categoria", id_cat).eq("id_usuario", user_id_str)` e rejeitar
   se não existir.
3. Reforçar com FK/constraint/RLS.
4. Testar com dois usuários.

## Critérios de aceite

- [ ] Não-dono recebe 403/404 em `pular_topico_edital`.
- [ ] Não-dono não consegue criar card em categoria alheia.
- [ ] Testes cobrem os dois cenários.
- [ ] Documentação de rotas reflete o comportamento real.
""",
    },
    {
        "title": "[Segurança] Markdown e |safe sem sanitização em múltiplas telas",
        "labels": "security, severity:low, frontend, xss, hardening",
        "body": """# [Segurança] Markdown e |safe sem sanitização em múltiplas telas

**Labels sugeridas:** `security`, `severity:low`, `frontend`, `xss`, `hardening`

## Descrição do problema

O projeto renderiza Markdown em HTML e injeta com `innerHTML` sem
sanitização em várias telas; também usa `|safe` em conteúdo dinâmico. Não
há biblioteca de sanitização nas dependências. Hoje o conteúdo é
majoritariamente gerado por IA, administrativo ou privado do próprio aluno,
então não foi confirmado vetor cross-user. É uma falha de defesa em
profundidade que se torna explorável se esse conteúdo passar a ser
compartilhado, importado ou influenciado por outro usuário.

## Evidência

```javascript
// static/js/questoes_common.js:98-105
let htmlRaw = marked.parse(textoProtegido, { breaks: true, gfm: true });
...
divTexto.innerHTML = htmlRaw;
```

```javascript
// static/js/aluno_estudar_edital.js:171-174
if (window.marked) {
    resultDiv.innerHTML = marked.parse(data.explicacao);
} else {
    resultDiv.innerHTML = data.explicacao.replace(/\\n/g, '<br>');
}
```

```javascript
// templates/resumos/ver_materia.html:147
el.innerHTML = marked.parse(raw, { breaks: true, gfm: true });
```

```html
<!-- templates/flashcards/gerenciar.html:35,38 -->
<div class="text-dark-emphasis mb-2 markdown-text">{{ card.frente|safe }}</div>
<div class="text-muted small markdown-text">{{ card.verso|safe }}</div>

<!-- templates/components/card_questao.html:20 -->
<p class="mb-3">{{ q.enunciado | safe}}</p>
```

## Por que é explorável

`marked.parse` não sanitiza HTML; a saída vai direto para `innerHTML`. Se
qualquer uma dessas fontes (IA, admin, importação, compartilhamento) passar
a aceitar conteúdo de outro usuário, o payload executa. A ausência de
sanitizador é a falha estrutural; o vetor concreto depende da evolução do
produto.

## Impacto

- Latente: XSS se conteúdo não confiável chegar às telas.
- Aumenta a superfície de ataque de qualquer feature futura de
  compartilhamento/importação.
- Dificulta a revisão de segurança de novos pontos de renderização.

## Sugestão de correção

1. Adicionar DOMPurify (frontend) e/ou bleach/nh3 (backend).
2. Sanitizar toda saída de Markdown antes de `innerHTML`.
3. Preferir `textContent` para conteúdo que não precisa de HTML.
4. Remover `|safe` de conteúdo dinâmico ou sanitizar antes do template.
5. Criar testes de payload para cada tela.

## Critérios de aceite

- [ ] Existe sanitizador nas dependências e ele é aplicado nos pontos
      listados.
- [ ] `|safe` não é usado em conteúdo de usuário/IA sem sanitização.
- [ ] Testes de XSS cobrem explicação, resumo, flashcard e enunciado.
- [ ] CSP sem `'unsafe-inline'` em `script-src`.
""",
    },
    {
        "title": "[Segurança] Segredos embarcados no cliente e higiene do .env",
        "labels": "security, severity:low, hardening, secrets",
        "body": """# [Segurança] Segredos embarcados no cliente e higiene do .env

**Labels sugeridas:** `security`, `severity:low`, `hardening`, `secrets`

## Descrição do problema

Há três pontos relacionados, com impactos diferentes:

1. A URL e a anon key do Supabase estão hardcoded no Electron e no site.
   A anon key é pública por design; não é um segredo vazado. O risco real é
   a policy de SELECT aberta (issue crítica).
2. O `APP_TOKEN` é carregado de `desktop/token.local.js` e foi encontrado
   no bundle `app.asar`. A documentação reconhece que ele é extraível.
   Como é compartilhado por todos os clientes, não identifica usuário e não
   deve ser a única barreira de escrita.
3. O `.env` local contém `FLASK_SECRET_KEY`, `APP_TOKEN` e uma
   `OPENAI_API_KEY` com valores reais. O arquivo é gitignored e nunca foi
   commitado; é higiene local, não vazamento de repositório.

## Evidência

```javascript
// desktop/main.js:26-27
const SUPABASE_URL = 'https://ivhuaevrrkrnagbqmnwc.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOi...';
```

```html
<!-- site/index.html:194-195 -->
var SUPABASE_URL = 'https://ivhuaevrrkrnagbqmnwc.supabase.co';
var SUPABASE_ANON_KEY = 'eyJhbGciOi...';
```

```javascript
// desktop/main.js:32-38
let APP_TOKEN;
try {
  ({ APP_TOKEN } = require('./token.local.js'));
} catch (e) {
  console.error('[shell] ERRO: desktop/token.local.js ausente...');
  process.exit(1);
}
```

```text
# .env:4,13,16 (valores reais; arquivo gitignored)
FLASK_SECRET_KEY=<64 hex>
APP_TOKEN=<64 hex>
OPENAI_API_KEY=sk-proj-...
```

## Por que é explorável

A anon key sozinha não dá escrita, mas dá leitura enquanto o RLS estiver
aberto. O `APP_TOKEN` é extraível do app.asar e compartilhado; quem o
extrair consegue replicar escritas do próprio usuário, mas não escrever
como outro aluno, porque o RLS também exige o JWT/dono. A `OPENAI_API_KEY`
local parece não ser usada pelo fluxo BYOK e deve ser removida.

## Impacto

- Anon key: habilitador da issue crítica de RLS; não é segredo.
- APP_TOKEN: falsa sensação de segurança; não é fronteira de autorização.
- .env: exposição local/backup; não há evidência de commit.

## Sugestão de correção

1. Corrigir o RLS (issue crítica) e documentar que a anon key é pública.
2. Tratar o `APP_TOKEN` como identificador de app, não segredo; manter
   `auth.uid()` + owner como barreira; rotacionar e registrar o processo.
3. Remover a `OPENAI_API_KEY` não usada do `.env`; rotacionar a
   `FLASK_SECRET_KEY` se o arquivo foi compartilhado.
4. Adicionar gitleaks no pre-commit/CI e revisar `.env.example`.

## Critérios de aceite

- [ ] A anon key não retorna dados de aluno (depende da issue de RLS).
- [ ] O APP_TOKEN não é descrito como segredo de autorização.
- [ ] Nenhuma chave OpenAI não usada permanece no `.env`.
- [ ] gitleaks roda no pre-commit/CI e o build falha em segredo detectado.
- [ ] `.env.example` contém apenas placeholders.
""",
    },
]
