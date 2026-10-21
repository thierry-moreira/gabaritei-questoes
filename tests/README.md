# Especificação da Suíte de Testes Unitários e Integração
## Gabaritei Questões

Este documento serve como guia técnico e especificação para a manutenção, execução e expansão futura da suíte de testes do projeto **Gabaritei Questões**. Os testes foram arquitetados para serem extremamente rápidos, leves e 100% isolados de serviços externos.

---

## 🛡️ Princípios de Design dos Testes

Para garantir a confiabilidade e a velocidade de execução da suíte, todos os testes devem seguir estritamente as diretrizes abaixo:

1. **Isolamento de Rede:** Nenhuma requisição HTTP real deve ser disparada durante a execução dos testes. Chamadas para APIs externas (como a API *Have I Been Pwned* ou serviços de IA) devem ser interceptadas e simuladas usando `unittest.mock`.
2. **Isolamento de Banco de Dados:** Nenhuma conexão real com o Supabase ou PostgreSQL deve ser efetuada. Interações com o banco de dados são mockadas simulando as respostas retornadas pelo wrapper `safe_execute` ou pela biblioteca do Supabase.
3. **Nativo e Leve:** A suíte de testes utiliza estritamente a biblioteca nativa `unittest` do Python. Isso elimina a necessidade de instalar pacotes adicionais e garante compatibilidade total com o ambiente existente.
4. **Sem Alterações na Infraestrutura:** Não é permitido modificar os arquivos `.env` ou `requirements.txt` apenas para fins de testes.

---

## 📂 Estrutura de Arquivos e Cobertura

A suíte de testes está localizada no diretório `tests/` e está organizada da seguinte forma:

```
caminho_do_projeto\tests\
├── __init__.py          # Inicializa o diretório como um módulo Python
├── test_modelos.py      # Testes de validação dos modelos e estruturas de dados
├── test_utils.py        # Testes de funções utilitárias e regras de negócio isoladas
├── test_rotas.py        # Testes de honeypots de segurança administrativa
├── test_auth.py         # Testes de autenticação, login, cadastro e sessões
├── test_aluno_questoes.py # Testes do dashboard, resolução, streaks e paywall (Fase 4)
├── test_ia_chat.py        # Testes de IA, explicações, resumos e flashcards (Fase 6)
├── test_conta.py          # Testes de atualização de perfil, reset de dados e exclusão de conta
├── test_api.py            # Testes de cascata de matérias, cargos e preferências de tema
├── test_flashcards.py     # Testes do sistema de flashcards e algoritmo Anki SM-2
├── test_caderno.py        # Testes de coleções de questões e limites de criação
└── test_resumos.py        # Testes do painel de resumos por matéria e exclusão
```

### 1. Modelos (`test_modelos.py`)
Valida o comportamento das classes de dados (representando tabelas e registros do Supabase), garantindo consistência na modelagem e lógica interna.
- **Classes testadas:** `User`, `UserMeta`, etc.
- **Foco:** Validação de inicialização de atributos, tipos de dados e lógica interna dos modelos sem persistência.

### 2. Utilitários (`test_utils.py`)
Garante o correto funcionamento de funções de suporte críticas e segurança do sistema.
- **Funções testadas:**
  - `slugify`: Geração de URLs amigáveis.

### 3. Honeypots de Segurança (`test_rotas.py`)
Valida as proteções preventivas contra acessos automatizados indevidos.
- **Rotas testadas:**
  - `/admin`, `/admin/` e `/admin/login` (honeypot de segurança que bloqueia acessos maliciosos com 404).

### 4. Autenticação e Sessões (`test_auth.py`)
Valida o fluxo completo de controle de acesso do aluno à plataforma.
- **Fluxos testados (modelo desktop, sem senha):**
  - Entrada automática: com usuário local existente, `/aluno/login` (GET) faz login e redireciona ao `/aluno/painel`; sem usuário, renderiza a tela de criação.
  - Criação do usuário local via `POST /aluno/criar` (sucesso, username vazio bloqueado com flash, conta existente entra direto sem duplicar).
  - Rotas removidas na migração desktop (cadastro, recuperação de senha, verificação de e-mail) respondendo 404; `POST /aluno/login` responde 405.
  - Fluxo de encerramento de sessão (`/logout`) limpando dados do aluno e preservando sessões administrativas protegidas.
- **Mocks importantes:**
  - `@patch('rotas.auth.current_user')` para injetar o estado do usuário logado/anônimo do Flask-Login.
  - `@patch('rotas.auth.safe_execute')` para simular o retorno de registros de usuários no banco de dados.

### 5. Ecossistema do Aluno e Questões (`test_aluno_questoes.py`) [Fase 4 - Consolidada]
Valida os dashboards de estatísticas do aluno, a lógica de resolução de questões com streaks e a barreira técnica de paywall para visitantes.
- **Fluxos testados:**
  - `/aluno/painel` (ofensiva/streak em Brasília, dados agregados por data, taxas de acerto).
  - `/aluno/dashboard_detalhado` (esquecimento, melhor matéria, redirecionamento se histórico estiver vazio).
  - `/aluno/responder` e `/api/responder` (envio de respostas, limites de grátis, incremento de streak no banco).
  - `/api/responder_publico` (paywall para visitantes limitando a 5 resoluções gratuitas na sessão).
  - `/api/comentarios` (moderação contra palavras inadequadas antes da inserção).
- **Mocks importantes:**
  - Simulação de histórico de respostas e tabelas do banco de dados no Supabase.
  - Sessão do Flask (`session['anon_questoes']`) para simulação de visitantes anônimos.

Valida as restrições rigorosas de segurança administrativa, fluxos de login com 2FA/TOTP multifator, controle de dispositivo único e CRUD taxonômico completo.
- **Fluxos testados:**
  - `/admin/dashboard` (redirecionamento de não administradores, renderização das contagens de taxonomia de questões).
  - Trava de dispositivo único (expulsão de login se o token na sessão não for compatível com o banco).
  - `/admin/login` (fluxo de credenciais corretas/incorretas, mitigação de Timing Attack via Dummy Hash).
  - `/admin/setup-2fa` (geração de QR Code em base64 e verificação inicial de chaves TOTP).
  - `/admin/verify-2fa` (validação de código TOTP ativo e gravação do novo token de sessão única).
  - `/api/gestao/add-materia` (inserção e retorno de nova matéria por admin autenticado).
  - `/admin/cadastro` (POST manual de cadastro de questão certo/errado, verificação de prova e gravação de alternativas).
- **Mocks importantes:**
  - Mock de `pyotp.TOTP` e geração em runtime de segredos base32 para validação real-time de tokens.
  - Simulação de tokens de segurança de sessão no banco e dados de taxonomia agregados de contagem de banco de dados.

### 6. Integração com IA (`test_ia_chat.py`) [Fase 6 - Consolidada]
Valida a lógica dos fluxos acionados por Inteligência Artificial na plataforma.
- **Fluxos testados:**
  - `/api/ia_explica` (validação de cache local `explicacoes_ia`, bloqueio de cota para planos sem IA ativa e geração bem-sucedida via OpenAI com limpeza de strings desnecessárias).
  - `/api/ia/gerar_estudo` (criação de resumos e flashcards, validação de cache de usuário em `resumos_estudo` ou `flashcards`, consulta a cache global `ia_cache_estudo` e gravação correta de novos materiais gerados).
- **Mocks importantes:**
  - Mock rigoroso do cliente oficial OpenAI (`client_gpt` em `rotas.questao`), cobrindo `chat.completions.create` retornando estruturas de escolhas e conteúdos fiéis.
  - Mock de banco de dados nas consultas de cache e persistência de materiais de IA.

### 7. Painel da Conta do Usuário (`test_conta.py`)
Valida as rotas de atualização de informações cadastrais do aluno, redefinição de dados de estudo e exclusão permanente de conta.
- **Fluxos testados:**
  - `/aluno/conta/` (GET para exibição da tela e POST para atualização de username e e-mail, sem senha).
  - `/aluno/conta/resetar-dados` (validação de frase secreta "RESETAR MEUS DADOS" e exclusão em massa das tabelas do Supabase de progresso do aluno).
  - `/aluno/conta/excluir` (validação de frase secreta "EXCLUIR MINHA CONTA", exclusão física de registros e logout da sessão).
- **Mocks importantes:**
  - Mock rigoroso das deleções em cascata de tabelas de histórico do Supabase via `safe_execute`.

### 8. APIs Dinâmicas do Sistema (`test_api.py`)
Valida os endpoints secundários que fornecem dados estruturados JSON e salvam preferências do usuário em tempo de execução.
- **Fluxos testados:**
  - `/api/cargos/<id_orgao>` (listagem ordenada de cargos com base no órgão público selecionado).
  - `/api/get_assuntos_cascata` (geração de estrutura hierárquica em árvore correlacionando matérias a tópicos e subtópicos associados).
  - `/api/topicos/<id_materia>` e `/api/subtopicos/<id_topico>` (listagem individual de taxonomia).
  - `/api/usuario/preferencias` (validação e salvamento de tema visual dark/light no banco).
- **Mocks importantes:**
  - Simulação de retornos encadeados de tópicos e subtópicos via `safe_execute`.
  - Simulação de updates e selects de preferências do perfil do usuário no Supabase.

### 9. Repetição Espaçada e Flashcards (`test_flashcards.py`)
Valida a segurança das rotas exclusivas para assinantes Premium, a criação de cards/categorias de estudo e a integridade matemática do algoritmo SM-2 (Anki).
- **Fluxos testados:**
  - `/aluno/flashcards` (dashboard inicial com listagem e contador de revisão).
  - `/aluno/flashcards/categoria/<id>` (gerenciamento e listagem de cards).
  - `/aluno/flashcards/estudar/<id>` (carregamento de cartões agendados).
  - `/api/flashcards/categoria/nova` e `/api/flashcards/criar` (criação e validação de nomes/perguntas).
  - `/api/flashcards/revisar` (algoritmo adaptativo SM-2 ajustando dinamicamente intervalo e fator de facilidade para qualidades 0, 1, 2 e 3).
  - Exclusão via APIs de categorias e cartões individuais.
- **Mocks importantes:**
  - Mock de `flask_login.utils._get_user` simulando estados do plano (`gratis` vs `premium`).
  - Simulação de retornos de inserção, deleção e queries de intervalo Supabase.

### 10. Coleções de Questões (`test_caderno.py`)
Valida as restrições de limites de criação de cadernos e a gestão individual de pastas de questões.
- **Fluxos testados:**
  - `/aluno/meus_cadernos` (painel geral com listagem de coleções).
  - `/aluno/caderno/<id>` (detalhamento integrado com histórico de acertos e erros).
  - `/api/cadernos/novo` (inserção e criação bem-sucedida de caderno).
  - `/api/cadernos/salvar` (inserção e captura de erro de chave estrangeira duplicada do Supabase).
  - Exclusão completa de cadernos e desvinculação individual de questões.
- **Mocks importantes:**
  - Injeção de estado `id_usuario` na sessão do Flask client.

### 11. Resumos Teóricos (`test_resumos.py`)
Valida o agrupamento de resumos teóricos por matérias e as barreiras técnicas de paywall associadas.
- **Fluxos testados:**
  - `/aluno/resumos` (dashboard agrupando quantidades de resumos por disciplina).
  - `/aluno/resumos/materia/<id>` (detalhamento de resumos com data de criação com tratamento de erro 404).
  - `/api/resumos/excluir/<id>` (remoção física de arquivos e registros).
- **Mocks importantes:**
  - Mock de `@premium_required` para redirecionamento resiliente de contas grátis.

---

## 🛠️ Padrões de Implementação (Guia de Manutenção)

Para manter os testes robustos durante modificações no código da aplicação, utilize os padrões de mock descritos a seguir:

### A. Simulação do Banco de Dados (`safe_execute`)
Como a aplicação utiliza a função centralizada `safe_execute` para consultas ao banco, você pode facilmente mockar consultas de login e carregamento de registros:

```python
@patch('rotas.auth.safe_execute')
def test_exemplo_consulta(self, mock_safe_execute):
    # Simula o retorno de um registro de usuário ativo no Supabase
    mock_res = MagicMock()
    mock_res.data = [{
        'id': 123,
        'email': 'teste@gabaritei.com',
        'role': 'aluno',
        'email_verificado': True
    }]
    mock_safe_execute.return_value = mock_res

    # Chame o cliente de testes ou a função que executa a query
    response = self.client.get('/alguma-rota-que-consulta')
```

### B. Simulação do Usuário Logado (`current_user`)
Para testar rotas que se comportam de forma diferente caso o usuário esteja autenticado ou não, mocke o objeto global `current_user`:

```python
@patch('rotas.auth.current_user')
def test_rota_protegida(self, mock_current_user):
    # Define o usuário como logado e com cargo de aluno
    mock_current_user.is_authenticated = True
    mock_current_user.role = 'aluno'
    
    response = self.client.get('/aluno/painel')
    self.assertEqual(response.status_code, 200)
```

### C. Captura e Verificação de Mensagens Flash
Muitas rotas utilizam `flash()` do Flask para exibir alertas. Você pode inspecionar a sessão do cliente de teste assim:

```python
response = self.client.post('/aluno/login', data={'email': 'errado@email.com', 'password': '123'})

# Abre a transação de sessão para ler os flashes gerados
with self.client.session_transaction() as sess:
    flashes = sess.get('_flashes', [])
    # Verifica se a mensagem de erro específica foi exibida
    self.assertTrue(any("E-mail ou senha" in msg[1] for msg in flashes))
```

### D. Mocking de Respostas de APIs JSON (`jsonify`)
Ao testar rotas que devolvem dados no formato JSON (como envios de resposta ou APIs de meta), você pode fazer requisições enviando dados em JSON e inspecionando o retorno direto do dicionário:

```python
# Simula uma requisição POST enviando JSON
response = self.client.post('/aluno/api/set-meta', json={"meta": 10})
self.assertEqual(response.status_code, 200)

# Obtém e valida o retorno JSON decodificado
dados_retorno = response.get_json()
self.assertTrue(dados_retorno.get('success'))
```

### E. Manipulação de Sessões do Flask (Paywall de Visitantes)
Para rotas que dependem de variáveis salvas na sessão do Flask (como o contador de questões anônimas do paywall), você pode injetar valores diretamente na sessão antes de fazer a chamada de teste:

```python
# Injeta 5 IDs de questões respondidas na sessão anônima para acionar o paywall
with self.client.session_transaction() as sess:
    sess['anon_questoes'] = [101, 102, 103, 104, 105]

# Tenta responder a uma nova questão (ID 106)
response = self.client.post('/api/responder_publico', json={
    "questao_id": 106,
    "alternativa": "A"
})

# Deve ser bloqueado pelo paywall retornando status 403
self.assertEqual(response.status_code, 403)
self.assertIn("Você atingiu o limite", response.get_json().get('error'))
```

---

## 🚀 Como Executar a Suíte de Testes

### 🖥️ No Windows (Console Nativo)
Um script de automação em lote (`.bat`) codificado em ASCII foi disponibilizado no diretório raiz do projeto para simplificar a execução.

Abra o prompt de comando (`cmd` ou `PowerShell`) na raiz do projeto e execute:
```cmd
.\rodar_testes.bat
```
Este script inicializa automaticamente o ambiente virtual (`venv`), roda todos os testes e exibe um sumário detalhado em cores na tela.

### 🐍 Usando Python Diretamente
Se preferir executar manualmente por linha de comando com o ambiente virtual ativado:
```bash
python -m unittest discover -s tests
```

Para rodar apenas um arquivo de teste específico:
```bash
python -m unittest tests/test_auth.py
```

---

## 📈 Futuras Expansões (Próximos Passos recomendados)

Ao adicionar novos recursos ao **Gabaritei Questões**, certifique-se de expandir a suíte seguindo estas fases propostas:

1. **Painel do Aluno e Questões (Fase 4 - Consolidada):** Cobertura completa de painéis estatísticos, cálculo de curvas de esquecimento, resolução de questões com streak e paywall de 5 questões.
2. **Integração com IA (Fase 6 - Consolidada):** Cobertura de explicações pedagógicas com suporte visual e persistência (/api/ia_explica), geração de resumos/flashcards (/api/ia/gerar_estudo) e gerenciamento de limites Trial.
