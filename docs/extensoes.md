# Documentação Técnica: `extensoes.py`

## Descrição Geral
O módulo `extensoes.py` centraliza a declaração, configuração e a inicialização de todos os serviços de terceiros, bibliotecas auxiliares do Flask (Segurança, Autenticação, Identidade e Sessões) e motores remotos de Inteligência Artificial. 

Esta centralização é uma excelente prática arquitetural que permite o registro tardio ("lazy initialization") das extensões no ciclo de vida do Flask, evitando problemas críticos de importações circulares entre rotas, modelos e o núcleo da aplicação.

---

## Componentes de Infraestrutura e Segurança

### 1. Segurança e Controle de Tráfego (Flask-Limiter)
- **Instância**: `limiter`
- **Estratégia de Captura**: Inicializado com `key_func=get_remote_address`, o qual extrai de forma automática o IP real dos clientes (integrado com cabeçalhos HTTP através do `ProxyFix` configurado no `app.py`).
- **Limites Padrão (Quotas)**:
  - `200 per day` (máximo de 200 requisições a cada 24 horas por cliente).
  - `50 per hour` (máximo de 50 requisições a cada 60 minutos por cliente).
- **Armazenamento de Estado (Storage)**: Configurado com `storage_uri="memory://"` (armazenamento volátil em memória local).
  > [!WARNING]
  > **Nota de Escalabilidade**: Em execução local/desktop (instância única), o armazenamento em memória é adequado. Caso a aplicação venha a ser executada em múltiplas instâncias simultâneas, o estado local ficaria inconsistente; nesse cenário, deve-se alterar a URI de armazenamento para um banco centralizado como Redis (`redis://[:senha]@host:porta/db`) para que os limites de IP sejam compartilhados entre todas as instâncias ativas.

### 2. Proteção contra CSRF (CSRFProtect)
- **Instância**: `csrf`
- **Propósito**: Habilita a proteção ativa global contra ataques de falsificação de solicitações entre sites (Cross-Site Request Forgery). Garante de forma automatizada que qualquer formulário submetido via método de escrita (POST, PUT, PATCH, DELETE) possua uma chave criptográfica originada única e exclusivamente pelo próprio servidor Gabaritei Questões.

### 3. Gestão de Identidade e Sessões (Flask-Login)
- **Instância**: `login_manager`
- **Comportamento e Redirecionamento**:
  - Usuários anônimos (não logados) que tentem forçar acesso a rotas restritas e protegidas por decorators serão imediatamente redirecionados para a tela de autenticação de alunos (`auth.login_aluno`).
  - **Mensagem Padrão de Bloqueio**: `"Por favor, faça login para acessar esta página."`
  - **Categoria de Alerta HTML**: `"info"` (renderizado dinamicamente nos templates via flash messages).

---

## Motores de Inteligência Artificial (OpenAI SDK)

O arquivo centraliza a criação e o apontamento dos modelos GPT oficiais, tratando a conexão de forma fail-safe (segura contra falhas) para que a ausência de chaves de API não impeça a aplicação de subir localmente em modo de desenvolvimento.

### 1. Cliente de IA Geral (Explicações e Resumos)
- **Instância**: `client_gpt`
- **Modelo Oficial**: `gpt-5.4-mini`
- **Configurações de Geração**: Temperatura fixada em `0.3` (`TEMPERATURE_GPT = 0.3`). Esta escolha técnica garante um equilíbrio excepcional para fins pedagógicos: restringe a "criatividade/alucinação" do modelo, priorizando respostas com máxima exatidão técnica, lógica de negócios precisa e explicações didáticas assertivas.
- **Fail-Safe**: Caso a variável `OPENAI_API_KEY` não seja localizada no ambiente, o sistema imprime logs de erro apropriados no console, mas permite que o servidor do Flask inicie suas demais operações normais.
