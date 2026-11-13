# -*- coding: utf-8 -*-
"""Dados verificados da auditoria de segurança do Gabaritei Questões.

Cada achado abaixo foi confirmado por leitura direta do código, da
documentação do projeto, do bundle Electron ou do histórico git. Onde a
evidência é documental (RLS), isso é dito explicitamente no campo
``condicao``. Nenhuma consulta foi executada contra a produção.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    fid: str
    severity: str
    category: str
    title: str
    location: str
    description: str
    impact: str
    fix: str
    condicao: str = ""


@dataclass(frozen=True)
class Category:
    code: str
    name: str
    mapping: str


CATEGORIES: list[Category] = [
    Category(
        "1",
        "Isolamento de inquilino/dono",
        "Supabase/PostgREST: policies RLS + filtros manuais por id_usuario nas rotas Flask.",
    ),
    Category(
        "2",
        "Permissão definida no navegador",
        "Flask-Login + aluno_required. Não existe UI administrativa neste repositório; "
        "o papel é fixado em 'aluno' no servidor.",
    ),
    Category(
        "3",
        "IDOR",
        "Rotas Flask que recebem id de objeto (path, query ou body) e deveriam validar o dono.",
    ),
    Category(
        "4",
        "Chaves expostas",
        ".env, histórico git, bundle Electron/app.asar, site público e configuração de build.",
    ),
    Category(
        "5",
        "Inputs sem tratamento (XSS)",
        "Jinja2 + JavaScript vanilla: innerHTML, marked.parse, |safe, CSP e ausência de sanitizador.",
    ),
]


FINDINGS: list[Finding] = [
    Finding(
        fid="F-01",
        severity="Crítica",
        category="1",
        title="RLS de SELECT aberta em 13 tabelas de dados do aluno",
        location="docs/banco_dados.md:27,38; desktop/main.js:26-27; site/index.html:194-195",
        description=(
            "A documentação do projeto declara SELECT livre para o papel anon em usuarios, "
            "historico_respostas, comentarios_questao, flashcards, flashcard_categorias, "
            "resumos_estudo, cadernos, caderno_questoes, filtros_salvos, simulados, "
            "simulados_questoes e simulados_resultados (além de editais_*). A anon key é "
            "pública e está embutida no cliente. Com ela, qualquer pessoa pode chamar o "
            "PostgREST e ler os dados de todos os alunos, sem login."
        ),
        impact=(
            "Exposição cross-tenant de e-mail/nome, histórico de respostas, comentários, "
            "flashcards, resumos, cadernos, filtros, simulados e resultados; base para "
            "phishing e para os IDORs encontrados."
        ),
        fix=(
            "Recriar as policies de SELECT como owner-only (auth.uid() = id_usuario, ou "
            "auth_id em usuarios); separar conteúdo público de dados de aluno; versionar "
            "as migrations de RLS neste repositório e testar com dois usuários e com a "
            "anon key sem JWT."
        ),
        condicao=(
            "Evidência documental: as migrations de RLS não estão no repositório. A "
            "exploração depende de a configuração descrita em docs/banco_dados.md estar "
            "vigente na produção. Nenhuma consulta real foi executada."
        ),
    ),
    Finding(
        fid="F-02",
        severity="Alta",
        category="3",
        title="IDOR na visualização de caderno",
        location="rotas/caderno.py:29-39",
        description=(
            "visualizar_caderno busca o nome do caderno por id_caderno (linha 33) e as "
            "questões por id_caderno (linha 37), sem filtrar por current_user.id. Também "
            "usa session.get('id_usuario') (linha 31) para o histórico. Qualquer aluno "
            "autenticado pode enumerar /aluno/caderno/<id> e ler cadernos alheios."
        ),
        impact="Leitura de conteúdo de estudo alheio; IDs numéricos são triviais de enumerar.",
        fix=(
            "Adicionar .eq('id_usuario', current_user.id) nas duas consultas, usar "
            "current_user.id no histórico e devolver 404 quando o caderno não for do usuário."
        ),
    ),
    Finding(
        fid="F-03",
        severity="Alta",
        category="3",
        title="Inserção cross-tenant em caderno alheio",
        location="rotas/caderno.py:114-125,37,168-174",
        description=(
            "salvar_na_pasta aceita id_caderno do corpo da requisição (linha 116) e insere "
            "em caderno_questoes com id_usuario=current_user.id (linha 122), sem validar se "
            "o caderno pertence ao usuário. A vítima vê a questão porque visualizar_caderno "
            "filtra só por id_caderno (linha 37); não consegue removê-la porque "
            "remover_questao_caderno filtra pelo id_usuario do chamador (linhas 168-174)."
        ),
        impact=(
            "Injeção/poluição persistente de cadernos alheios, de difícil remoção pela vítima."
        ),
        fix=(
            "Validar a posse do caderno antes do insert; reforçar no banco com FK/constraint "
            "ou policy que amarre caderno_questoes.id_usuario ao dono de cadernos.id_usuario."
        ),
    ),
    Finding(
        fid="F-04",
        severity="Alta",
        category="3",
        title="Correção de simulado privado sem verificação de dono",
        location="rotas/simulado.py:186-220,224-230",
        description=(
            "corrigir_simulado carrega o simulado por ID (linha 188), calcula o gabarito "
            "(194-201) e devolve resposta_correta no resultado (215-220), sem repetir a "
            "checagem de eh_privado/id_criador existente em fazer_simulado (145-147). "
            "Qualquer aluno autenticado pode dar POST em /aluno/simulados/corrigir/<id> de "
            "um simulado privado alheio e obter o gabarito; o insert em "
            "simulados_resultados (224-230) também é aceito."
        ),
        impact="Quebra do sigilo do simulado privado, exposição do gabarito e ranking poluído.",
        fix=(
            "Extrair um guard único (_simulado_do_usuario_ou_404) e chamá-lo em corrigir, "
            "ranking e PDF antes de qualquer consulta de questões/resultados."
        ),
    ),
    Finding(
        fid="F-05",
        severity="Média",
        category="3",
        title="Ranking de simulado privado exposto",
        location="rotas/simulado.py:278-296",
        description=(
            "ver_ranking_simulado busca titulo, eh_privado (280-282), mas não compara "
            "eh_privado/id_criador com current_user; em seguida lista resultados e usernames "
            "(289-296). Qualquer aluno autenticado com o ID vê o ranking de um simulado "
            "privado alheio."
        ),
        impact="Exposição de participantes, notas e desempenho de um simulado privado.",
        fix=(
            "Aplicar o mesmo guard de dono; para simulado privado, permitir ranking apenas "
            "ao criador ou desabilitar a tela."
        ),
    ),
    Finding(
        fid="F-06",
        severity="Alta",
        category="3",
        title="PDF de simulado privado expõe questões e gabarito",
        location="rotas/simulado.py:310-319,351-360",
        description=(
            "baixar_pdf_simulado busca o simulado por ID (312-314) e monta a prévia com "
            "questões/alternativas (321-360), incluindo letra_gabarito (351-360), sem checar "
            "eh_privado/id_criador. Qualquer aluno autenticado pode acessar "
            "/simulado/<id>/pdf de um simulado privado alheio e obter a prova e o gabarito."
        ),
        impact="Vazamento de conteúdo e gabarito de simulados privados.",
        fix="Aplicar o guard de dono antes de buscar questões e alternativas; testar não-dono.",
    ),
    Finding(
        fid="F-07",
        severity="Média",
        category="1",
        title="Endpoint público de comentários retorna id_usuario",
        location="rotas/questao.py:311-320,350",
        description=(
            "GET /api/comentarios/<id_questao> não exige autenticação, usa select('*') "
            "(314-316) e devolve todas as colunas, incluindo id_usuario (350). Isso entrega "
            "UUIDs de alunos a qualquer visitante e serve de pivô para as tabelas com SELECT "
            "aberto."
        ),
        impact="Exposição de identificadores e facilitação de correlação com usuarios e outros dados.",
        fix=(
            "Selecionar colunas explícitas (id_comentario, nome_usuario, texto_comentario, "
            "criado_em), nunca retornar id_usuario, limitar/paginar e aplicar rate limit."
        ),
    ),
    Finding(
        fid="F-08",
        severity="Média",
        category="2",
        title="/api/responder confia no is_correct enviado pelo cliente",
        location="rotas/questao.py:287-301",
        description=(
            "O endpoint lê is_correct do JSON (linha 294) e grava diretamente em "
            "historico_respostas (296-301). O cliente pode enviar true para qualquer "
            "resposta, inflando acertos, ofensiva e estatísticas. A rota principal "
            "/aluno/responder calcula a correção no servidor (33-47), mas essa rota "
            "alternativa permanece e não é chamada pelo frontend atual."
        ),
        impact="Integridade de progresso/estatísticas; possível manipulação de indicadores derivados.",
        fix=(
            "Ignorar is_correct do cliente e calcular no servidor como /aluno/responder; se a "
            "rota for legada, removê-la."
        ),
    ),
    Finding(
        fid="F-09",
        severity="Baixa",
        category="3",
        title="pular_topico_edital sem verificação de dono",
        location="rotas/edital.py:578-583,157-160",
        description=(
            "A rota recebe id_edital (578-583) e chama _avancar_ciclo_edital sem checar "
            "editais_ciclo.id_usuario. A função consulta editais_progresso só por id_edital "
            "(157-160). Hoje o RLS owner-only das tabelas de progresso (docs:29) impede o "
            "cross-tenant, mas a ausência de check é uma regressão latente."
        ),
        impact="Se o RLS for afrouxado/alterado, um aluno avança o ciclo de outro.",
        fix="Adicionar checagem de posse como em responder_edital (485-490) antes de chamar a função.",
    ),
    Finding(
        fid="F-10",
        severity="Baixa",
        category="3",
        title="criar_card aceita id_categoria de outro usuário",
        location="rotas/flashcards.py:114-133,50-54",
        description=(
            "A rota lê id_categoria do JSON (118) e insere o flashcard com "
            "id_usuario=current_user.id (127-133), sem validar se a categoria pertence ao "
            "usuário. O card não aparece na lista da vítima (filtro por id_usuario em 52-53), "
            "mas cria referência órfã/cross-tenant e permite poluir categorias alheias."
        ),
        impact="Baixo; integridade referencial e possível confusão de dados.",
        fix="Validar a posse da categoria antes do insert; reforçar com FK/constraint/RLS.",
    ),
    Finding(
        fid="F-11",
        severity="Alta",
        category="5",
        title="XSS armazenado em comentários (texto e nome de usuário)",
        location=(
            "rotas/questao.py:326-354,311-320; static/js/questoes_common.js:229-238; "
            "app.py:146-151; rotas/conta.py:35-44"
        ),
        description=(
            "salvar_comentario grava texto e nome_usuario sem sanitização (348-353). O "
            "nome_usuario vem de usuarios.username, editável em /aluno/conta/ (conta.py:35-44). "
            "A listagem pública busca os comentários (311-320) e o JS monta HTML com template "
            "literals e innerHTML (229-238), interpolando nome_usuario (232) e "
            "texto_comentario (235). Não há DOMPurify/bleach/nh3 no projeto; o CSP permite "
            "'unsafe-inline' em script-src (app.py:146-151), então <img src=x onerror=...> "
            "executa. O payload é armazenado e disparado para qualquer usuário que expanda "
            "os comentários da questão."
        ),
        impact=(
            "Execução de JS no contexto do app; ações como a vítima, leitura de dados e "
            "exfiltração. Em Electron, contextIsolation/sandbox limitam o acesso ao Node, "
            "mas não ao mesmo-origin."
        ),
        fix=(
            "Sanitizar na saída com DOMPurify (allowlist) e/ou no servidor com bleach/nh3; "
            "renderizar nome/texto com textContent; remover 'unsafe-inline' do CSP usando "
            "nonces/hashes; adicionar object-src 'none' e base-uri 'self'."
        ),
    ),
    Finding(
        fid="F-12",
        severity="Baixa",
        category="5",
        title="Markdown e |safe sem sanitização em múltiplas superfícies",
        location=(
            "static/js/questoes_common.js:98-105; static/js/aluno_estudar_edital.js:171-174; "
            "templates/resumos/ver_materia.html:147; templates/flashcards/estudar.html:116-117; "
            "templates/flashcards/gerenciar.html:35,38; templates/components/card_questao.html:20"
        ),
        description=(
            "O projeto renderiza Markdown em HTML e injeta com innerHTML sem sanitização em "
            "explicações de IA, editais, resumos e flashcards; também usa |safe em flashcards "
            "e no enunciado da questão. Não há biblioteca de sanitização nas dependências. "
            "Hoje o conteúdo é majoritariamente gerado por IA, administrativo ou privado do "
            "próprio aluno, então não foi confirmado vetor cross-user; é falha de defesa em "
            "profundidade que se torna explorável se esse conteúdo passar a ser "
            "compartilhado/importado."
        ),
        impact="Latente; XSS se conteúdo não confiável chegar a essas superfícies.",
        fix=(
            "Sanitizar todo HTML de saída; preferir textContent; allowlist de Markdown; "
            "adicionar DOMPurify/bleach e testes de payload."
        ),
    ),
    Finding(
        fid="F-13",
        severity="Informativa",
        category="4",
        title="Anon key e URL do Supabase hardcoded no cliente",
        location="desktop/main.js:26-27; site/index.html:194-195",
        description=(
            "A URL e a anon key do Supabase estão embutidas no shell Electron e na página "
            "pública. A anon key é pública por design (JWT role=anon) e não deve ser tratada "
            "como segredo; o risco real é a policy de SELECT aberta (F-01). Não há "
            "service_role no repositório."
        ),
        impact="Informativa; é o habilitador de F-01, não um segredo vazado.",
        fix=(
            "Manter pública se o RLS for corrigido; documentar que não é segredo; monitorar "
            "uso e não rotacionar como se fosse credencial privilegiada."
        ),
    ),
    Finding(
        fid="F-14",
        severity="Baixa",
        category="4",
        title="APP_TOKEN embarcado no cliente não é fronteira de autorização",
        location="desktop/main.js:32-38; desktop/token.local.js:3; desktop/dist/win-unpacked/resources/app.asar",
        description=(
            "O shell carrega desktop/token.local.js; o token está na linha 3 e foi "
            "encontrado no bundle app.asar. A documentação reconhece que ele é extraível "
            "(docs/banco_dados.md:36). Como é compartilhado por todos os clientes, não "
            "identifica usuário e não deve ser a única barreira de escrita."
        ),
        impact="Baixa; permite replicar escritas do próprio usuário, mas não escrever como outro.",
        fix=(
            "Tratar como identificador de app, não segredo; manter auth.uid() + owner como "
            "barreira; rotacionar; considerar attestation/assinatura."
        ),
    ),
    Finding(
        fid="F-15",
        severity="Informativa",
        category="4",
        title="Segredos locais em texto puro no .env",
        location=".env:4,13,16",
        description=(
            ".env contém FLASK_SECRET_KEY (linha 4), APP_TOKEN (13) e OPENAI_API_KEY (16) "
            "com valores reais. O arquivo é gitignored e nunca foi commitado (verificado com "
            "git log --all -- .env e git ls-files), então não é vazamento de repositório. É "
            "higiene: a chave OpenAI parece não ser usada pelo fluxo BYOK e deve ser "
            "removida/rotacionada; a FLASK_SECRET_KEY deve ser rotacionada se o arquivo foi "
            "compartilhado."
        ),
        impact="Informativa; exposição local/backup, não exposição no git.",
        fix=(
            "Remover a OPENAI_API_KEY não usada; rotacionar; usar cofre/DPAPI; adicionar "
            "gitleaks no pre-commit."
        ),
    ),
]


STRENGTHS: list[tuple[str, str, str]] = [
    (
        "CSRF global em todas as rotas de escrita",
        "extensoes.py:12; app.py:140",
        "CSRFProtect é inicializado globalmente e não há csrf.exempt no projeto. Formulários "
        "incluem csrf_token() e o AJAX envia X-CSRFToken (conta.html:307-385; "
        "questoes_common.js:27-163).",
    ),
    (
        "Autorização de papel no servidor, não no navegador",
        "utils.py:63-70; app.py:316-321; rotas/auth.py:36-41",
        "aluno_required valida is_authenticated e role == 'aluno' no backend; o papel é "
        "fixado em 'aluno' no load_user e no login. Não existe UI administrativa nem rota "
        "privilegiada neste repositório.",
    ),
    (
        "Correção de respostas calculada no servidor",
        "rotas/questao.py:33-47; rotas/edital.py:493-501",
        "A rota principal /aluno/responder e responder_edital buscam as alternativas e "
        "comparam a letra no servidor; o cliente não decide o acerto (a exceção é a rota "
        "legada /api/responder, achado F-08).",
    ),
    (
        "Filtros de dono na maior parte do CRUD",
        "caderno.py:16,80,138-141,168-174; flashcards.py:17-19,43,52-53,78,162-167; "
        "resumos.py:14,40,50,60; filtro.py:24,45; edital.py:291,384-393,485-490,603-610,717",
        "Listagens, exclusões e updates de cadernos, flashcards, resumos, filtros, editais e "
        "simulados aplicam id_usuario/id_criador do usuário autenticado. A matriz de "
        "cobertura no apêndice detalha rota a rota.",
    ),
    (
        "Bloqueio de simulado privado na rota de realização",
        "rotas/simulado.py:145-147",
        "fazer_simulado compara eh_privado e id_criador com current_user.id antes de "
        "carregar questões. O padrão correto existe, mas não foi replicado em corrigir, "
        "ranking e PDF (F-04 a F-06).",
    ),
    (
        "Fail-fast para segredos obrigatórios",
        "app.py:64-68; banco_dados_aluno.py:24-27",
        "A aplicação encerra se FLASK_SECRET_KEY, SUPABASE_URL, SUPABASE_ANON_KEY ou "
        "APP_TOKEN faltarem. Não há fallback do tipo ${VAR:-valor-default}.",
    ),
    (
        "Nenhum segredo real commitado no histórico git",
        "git log --all -- .env; git ls-files",
        ".env e desktop/token.local.js nunca foram rastreados; o único sk-proj- do histórico "
        "é o placeholder 'sk-proj-sua-chave-openai-aqui' em .env.example. A service_role não "
        "aparece no repositório.",
    ),
    (
        "Jinja2 com autoescape e site público sem sink DOM",
        "templates/*.html; site/index.html:214-279",
        "A maior parte das saídas usa {{ }} com autoescape. O site de confirmação usa "
        "textContent para mensagens de erro, sem innerHTML com dados do usuário.",
    ),
    (
        "Hardening do Electron",
        "desktop/main.js:135-139",
        "contextIsolation: true, nodeIntegration: false e sandbox: true reduzem o impacto "
        "de um XSS no renderer, embora não impeçam ações same-origin.",
    ),
    (
        "Mensagens de autenticação genéricas e senha mínima",
        "rotas/auth.py:17,150-153,223-225",
        "Login inválido não revela se o e-mail existe; reset de senha usa mensagem genérica; "
        "a senha mínima é 8 caracteres.",
    ),
    (
        "Superfície de rede restrita ao loopback",
        "app.py:332",
        "O servidor de desenvolvimento sobe em 127.0.0.1:5000; não há Docker/CI/Helm/"
        "Terraform no repositório que exponha a aplicação por padrão.",
    ),
    (
        "Escrita do aluno exige token + identidade do dono (documentado)",
        "docs/banco_dados.md:29,36",
        "As policies de escrita descritas exigem eh_app_aluno() e eh_dono_do_aluno(...); "
        "mesmo com anon key + APP_TOKEN, a escrita em nome de outro aluno é bloqueada. "
        "Evidência documental, não SQL executado.",
    ),
]


WEAKNESSES: list[tuple[str, str, str]] = [
    (
        "Crítica",
        "O SELECT é a porteira aberta",
        "A privacidade entre alunos não é garantida em SELECT. A anon key pública transforma "
        "a leitura em um dump cross-tenant sem autenticação. É o risco sistêmico que "
        "prevalece sobre os demais.",
    ),
    (
        "Alta",
        "IDORs de aplicação sobrevivem ao RLS",
        "Cadernos e simulados privados têm consultas por ID sem dono. Mesmo que o RLS de "
        "SELECT seja corrigido, essas rotas continuam vazando ou aceitando escrita "
        "cross-tenant.",
    ),
    (
        "Alta",
        "XSS armazenado em comentários",
        "Texto e nome de usuário entram crus no innerHTML. O CSP com unsafe-inline permite "
        "o onerror. O payload atinge qualquer leitor da questão, não só o autor.",
    ),
    (
        "Média",
        "Placar confiado ao cliente na rota legada",
        "/api/responder aceita is_correct do JSON. A rota principal está correta, mas a "
        "alternativa permite forjar histórico e estatísticas.",
    ),
    (
        "Baixa",
        "APP_TOKEN não é uma fronteira real",
        "O token é compartilhado e extraível do app.asar. Ele fecha o curl fácil, mas não "
        "identifica usuário; a barreira real precisa ser o JWT + owner no banco.",
    ),
    (
        "Informativa",
        "Documentação promete mais do que o código entrega",
        "docs/rotas/caderno.md:111-112 e docs/rotas/simulado.py.md:100,152 afirmam "
        "verificação compulsória de dono em todas as rotas; o código contradiz em cadernos "
        "e em três rotas de simulado.",
    ),
]


RECOMMENDATIONS: list[tuple[str, str, str, str]] = [
    (
        "P1",
        "Fechar o SELECT cross-tenant no Supabase",
        "Recriar as policies de SELECT das tabelas de aluno como owner-only; separar "
        "conteúdo público; versionar as migrations; validar com anon key e com dois usuários.",
        "F-01, F-07",
    ),
    (
        "P1",
        "Corrigir os IDORs de cadernos",
        "Adicionar id_usuario em visualizar_caderno e validar a posse do caderno em "
        "salvar_na_pasta; reforçar no banco.",
        "F-02, F-03",
    ),
    (
        "P1",
        "Proteger simulados privados nas três rotas",
        "Aplicar o mesmo guard de fazer_simulado em corrigir, ranking e PDF; devolver 404 "
        "para não-dono antes de qualquer consulta.",
        "F-04, F-05, F-06",
    ),
    (
        "P1",
        "Eliminar o XSS armazenado de comentários",
        "Sanitizar na saída (DOMPurify/bleach), usar textContent para nome/texto e remover "
        "unsafe-inline do CSP com nonces/hashes.",
        "F-11",
    ),
    (
        "P1",
        "Remover ou corrigir /api/responder",
        "Calcular is_correct no servidor ou apagar a rota legada; adicionar teste que "
        "envia true para uma resposta errada.",
        "F-08",
    ),
    (
        "P2",
        "Reduzir a exposição do endpoint de comentários",
        "Selecionar colunas explícitas, não devolver id_usuario, paginar e limitar a taxa.",
        "F-07",
    ),
    (
        "P2",
        "Fechar checks de posse em editais e flashcards",
        "Adicionar o guard de dono em pular_topico_edital e validar id_categoria em "
        "criar_card; teste com dois usuários.",
        "F-09, F-10",
    ),
    (
        "P2",
        "Sanitizar Markdown e remover |safe de conteúdo dinâmico",
        "Aplicar allowlist de Markdown, DOMPurify/bleach e testes de payload em explicações, "
        "resumos, flashcards e enunciados.",
        "F-12",
    ),
    (
        "P2",
        "Reposicionar o APP_TOKEN e limpar segredos locais",
        "Tratar o token como identificador de app; manter JWT + owner como barreira; "
        "remover a OPENAI_API_KEY não usada e rotacionar o que foi compartilhado.",
        "F-14, F-15",
    ),
    (
        "P2",
        "Adicionar verificação de segredos no fluxo de desenvolvimento",
        "gitleaks no pre-commit/CI, pip-audit/npm audit e revisão do .env.example.",
        "F-13, F-14, F-15",
    ),
    (
        "P3",
        "Criar testes de regressão cross-tenant",
        "Dois usuários de teste: B não lê/edita A em cadernos, simulados, editais, "
        "flashcards e resumos; anon não lê dados de aluno.",
        "F-01 a F-10",
    ),
    (
        "P3",
        "Adicionar análise estática e SCA no CI",
        "bandit/semgrep para Python, eslint-plugin-security para JS, pip-audit e npm audit; "
        "falhar o build em achados altos.",
        "Transversal",
    ),
    (
        "P3",
        "Versionar e testar as policies RLS",
        "Migrations no repo, script de teste com anon/authenticated e documentação de "
        "exceções de leitura pública.",
        "F-01",
    ),
    (
        "P3",
        "Auditar logs e dados sensíveis",
        "Não logar session/refresh token; revisar logs de login e de queries; mascarar "
        "e-mail/UUID em telemetria.",
        "Transversal",
    ),
]


ROUTES: list[tuple[str, str, str, str]] = [
    ("GET /aluno/caderno/<id_caderno>", "rotas/caderno.py:26", "Nenhum (só id_caderno)", "IDOR"),
    ("POST /api/cadernos/salvar", "rotas/caderno.py:111", "Nenhum no id_caderno", "IDOR"),
    ("POST /api/cadernos/excluir/<id_caderno>", "rotas/caderno.py:134", "id_usuario", "OK"),
    ("POST /api/cadernos/remover_questao", "rotas/caderno.py:150", "id_usuario", "OK"),
    ("GET /aluno/simulados/fazer/<id>", "rotas/simulado.py:132", "eh_privado + id_criador", "OK"),
    ("POST /aluno/simulados/corrigir/<id>", "rotas/simulado.py:183", "Nenhum", "IDOR"),
    ("POST /aluno/simulados/excluir/<id>", "rotas/simulado.py:256", "id_criador", "OK"),
    ("GET /aluno/simulados/ranking/<id>", "rotas/simulado.py:275", "Nenhum", "IDOR"),
    ("GET /simulado/<id>/pdf", "rotas/simulado.py:307", "Nenhum", "IDOR"),
    ("GET /aluno/editais/estudar/<id>", "rotas/edital.py:379", "id_usuario", "OK"),
    ("POST /aluno/editais/responder", "rotas/edital.py:476", "id_usuario", "OK"),
    ("POST /aluno/editais/pular/<id>", "rotas/edital.py:578", "Nenhum (RLS mitiga)", "Risco latente"),
    ("GET /aluno/editais/dashboard/<id>", "rotas/edital.py:598", "id_usuario", "OK"),
    ("POST /aluno/editais/excluir/<id>", "rotas/edital.py:712", "id_usuario", "OK"),
    ("GET /aluno/flashcards/categoria/<id>", "rotas/flashcards.py:38", "id_usuario", "OK"),
    ("POST /api/flashcards/criar", "rotas/flashcards.py:114", "id_categoria não validado", "Baixo"),
    ("POST /api/flashcards/revisar", "rotas/flashcards.py:140", "id_usuario", "OK"),
    ("POST /api/flashcards/excluir/<id>", "rotas/flashcards.py:213", "id_usuario", "OK"),
    ("POST /api/flashcards/categoria/excluir/<id>", "rotas/flashcards.py:223", "id_usuario", "OK"),
    ("GET /aluno/resumos/materia/<id>", "rotas/resumos.py:31", "id_usuario", "OK"),
    ("POST /api/resumos/excluir/<id>", "rotas/resumos.py:46", "id_usuario", "OK"),
    ("POST /api/resumos/excluir-materia/<id>", "rotas/resumos.py:56", "id_usuario", "OK"),
    ("POST /aluno/excluir_filtro/<id>", "rotas/filtro.py:36", "id_usuario", "OK"),
    ("POST /aluno/api/set-meta", "rotas/aluno.py:171", "current_user.id", "OK"),
    ("POST /api/usuario/preferencias", "rotas/api.py:106", "current_user.id", "OK"),
    ("POST /aluno/conta/", "rotas/conta.py:31", "current_user.id", "OK"),
    ("POST /aluno/conta/resetar-dados", "rotas/conta.py:110", "current_user.id", "OK"),
    ("POST /aluno/conta/excluir", "rotas/conta.py:158", "current_user.id", "OK"),
    ("POST /aluno/responder", "rotas/questao.py:24", "current_user.id + score server-side", "OK"),
    ("POST /api/responder", "rotas/questao.py:287", "current_user.id, mas is_correct do cliente", "Falha de integridade"),
    ("GET /api/comentarios/<id>", "rotas/questao.py:311", "Público; devolve id_usuario", "Exposição"),
    ("POST /api/comentarios", "rotas/questao.py:326", "current_user.id", "OK (mas XSS)"),
    ("POST /api/comentarios/<id>/reportar", "rotas/questao.py:363", "current_user.id", "OK"),
    ("POST /api/ia/config", "rotas/conta.py:66", "current_user.id", "OK"),
    ("POST /api/ia/config/remover", "rotas/conta.py:102", "current_user.id", "OK"),
]


# Trechos exatos que sustentam cada achado. O conteúdo foi copiado do
# repositório; reticências indicam omissão deliberada de linhas intermediárias
# ou de valores sensíveis (chaves nunca são reproduzidas por inteiro).
TRECHOS: dict[str, str] = {
    "F-01": """# docs/banco_dados.md:27
"Dados do aluno (16 tabelas: usuarios, historico_respostas,
 comentarios_questao, flashcards, ...): SELECT livre ..."

# docs/banco_dados.md:38
"a leitura dos dados de estudo é liberada pelo desenho atual
 (privacidade entre alunos não é garantida em SELECT, com
 exceção das 3 tabelas de edital)" """,
    "F-02": """# rotas/caderno.py:33
query_nome = supabase.table("cadernos").select("nome_caderno").eq("id_caderno", id_caderno).single()

# rotas/caderno.py:37
query_ids = supabase.table("caderno_questoes").select("id_questao").eq("id_caderno", id_caderno)

# nenhum filtro por current_user.id / id_usuario""",
    "F-03": """# rotas/caderno.py:116
id_caderno = dados.get('id_caderno')

# rotas/caderno.py:119-123
supabase.table("caderno_questoes").insert({
    "id_caderno": id_caderno,
    "id_questao": id_questao,
    "id_usuario": current_user.id
})""",
    "F-04": """# rotas/simulado.py:188
res_simulado = safe_execute(
    supabase.table('simulados').select('*').eq('id', id_simulado).single())
# ^ nenhum check de eh_privado / id_criador

# rotas/simulado.py:215-220
detalhes_resultado.append({
    'id_questao': q_id,
    'resposta_aluno': resposta_aluno,
    'resposta_correta': correta,
    'correto': eh_correto
})""",
    "F-05": """# rotas/simulado.py:280-282
res_simulado = safe_execute(
    supabase.table('simulados').select('titulo, eh_privado').eq('id', id_simulado).single()
)
# ^ busca eh_privado, mas nao compara com current_user

# rotas/simulado.py:289-295
res_ranking = safe_execute(
    supabase.table('simulados_resultados')
    .select('nota, respostas_corretas, total_questoes, data_conclusao, usuarios(username)')
    .eq('id_simulado', id_simulado)
    .order('nota', desc=True)
    .limit(50))""",
    "F-06": """# rotas/simulado.py:312-314
res_simulado = safe_execute(
    supabase.table('simulados').select('*').eq('id', id_simulado).single()
)
# ^ nenhum check de eh_privado / id_criador

# rotas/simulado.py:360
q['letra_gabarito'] = letra_certa if letra_certa else 'N/A'""",
    "F-07": """# rotas/questao.py:314-320
query_comentarios = supabase.table("comentarios_questao") \\
    .select("*") \\
    .eq("id_questao", id_questao) \\
    .order("criado_em", desc=True)
res = safe_execute(query_comentarios)
return jsonify(res.data if res.data else [])""",
    "F-08": """# rotas/questao.py:294
is_correct = data.get('is_correct')

# rotas/questao.py:296-301
query_historico = supabase.table("historico_respostas").insert({
    "id_usuario": current_user.id,
    "id_questao": id_questao,
    "id_alternativa_marcada": id_alternativa,
    "is_correct": is_correct
})""",
    "F-09": """# rotas/edital.py:581-583
def pular_topico_edital(id_edital):
    success, msg, _ = _avancar_ciclo_edital(id_edital, marcar_concluido=True)

# rotas/edital.py:157-160: _avancar_ciclo_edital busca o progresso
res_prog = safe_execute(
    supabase.table("editais_progresso").select("*").eq("id_edital", id_edital).single())""",
    "F-10": """# rotas/flashcards.py:118
id_cat = dados.get('id_categoria')

# rotas/flashcards.py:127-133
query = supabase.table("flashcards").insert({
    "id_usuario": user_id_str,
    "id_categoria": id_cat,
    "frente": frente,
    "verso": verso,
    "proxima_revisao": datetime.now().isoformat()
})""",
    "F-11": """// static/js/questoes_common.js:229-238
html += `
  <div class="mb-2 p-2 bg-white rounded border shadow-sm text-dark">
    <strong class="small text-primary">... ${comentario.nome_usuario || 'Aluno'}</strong>
    <p class="mb-0 small">${comentario.texto_comentario || comentario.texto || ''}</p>
  </div>`;
...
divLista.innerHTML = html;""",
    "F-12": """// static/js/questoes_common.js:98,105
let htmlRaw = marked.parse(textoProtegido, { breaks: true, gfm: true });
...
divTexto.innerHTML = htmlRaw;

<!-- templates/flashcards/gerenciar.html:35,38 -->
<div class="markdown-text">{{ card.frente|safe }}</div>
<div class="markdown-text">{{ card.verso|safe }}</div>""",
    "F-13": """// desktop/main.js:26-27
const SUPABASE_URL = 'https://ivhuaevrrkrnagbqmnwc.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';

<!-- site/index.html:194-195 -->
var SUPABASE_URL = 'https://ivhuaevrrkrnagbqmnwc.supabase.co';
var SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';""",
    "F-14": """// desktop/main.js:32-38
let APP_TOKEN;
try {
  ({ APP_TOKEN } = require('./token.local.js'));
} catch (e) {
  console.error('[shell] ERRO: desktop/token.local.js ausente...');
  process.exit(1);
}
// O token foi localizado no bundle: desktop/dist/win-unpacked/resources/app.asar""",
    "F-15": """# .env:4,13,16 (valores reais; arquivo gitignored)
FLASK_SECRET_KEY=<64 hex>
APP_TOKEN=<64 hex>
OPENAI_API_KEY=sk-proj-...""",
}
