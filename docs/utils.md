# Documentação Técnica: `utils.py`

## Descrição Geral
O módulo `utils.py` é o núcleo de inteligência auxiliar, segurança e utilitários transversais da plataforma. Ele reúne decorators de controle de rotas por perfis de acesso, tratativas de resiliência em banco de dados, filtros de moderação inteligente de texto e serviços dinâmicos de envio de e-mails via protocolo SMTP.

---

## 1. Resiliência de Infraestrutura e Rede

### `safe_execute(query_func)`
- **Propósito**: Camada de resiliência sobre chamadas síncronas ao Supabase (PostgREST).
- **Lógica de Retentativa (Retry)**: Tenta executar a consulta fornecida até 3 vezes caso ocorra uma falha técnica momentânea de rede ou conexão.
- **Delay Exponencial**: Aplica uma pausa estática de `0.5` segundos entre tentativas malsucedidas.
- **Tratamento de Exceções**: Se a falha persistir após a terceira tentativa, o sistema registra um log de erro crítico (`logger.error`) detalhado e propaga o erro de forma visível para facilitar o diagnóstico de auditoria.

### `pegar_ip_real()`
- **Propósito**: Retorna o IP real do cliente.
- **Implementação**: Acessa `request.remote_addr` que é normalizado pelo middleware `ProxyFix` no arquivo `app.py`.

### `get_base_url()`
- **Propósito**: Retorna a URL base da aplicação.
- **Lógica**: Aplicação local/desktop — usa sempre a origem da própria requisição (`request.host_url`), compatível com execução em HTTP puro.

---

## 2. Prevenção de Abuso e Validação de Motores de Busca

### `verificar_bot_real(ip, user_agent)`
- **Propósito**: Garante que requisições que se passem por robôs de busca (como Googlebot ou Bingbot) sejam de fato legítimas, evitando ataques disfarçados (spoofing).
- **Algoritmo de Verificação (Reverse DNS)**:
  1. Captura o IP e valida se o cabeçalho `User-Agent` contém `"googlebot"` ou `"bingbot"`.
  2. Executa um Reverse DNS (`socket.gethostbyaddr`) no IP para capturar o hostname registrado (que deve pertencer estritamente a domínios como `.googlebot.com`, `.google.com` ou `.search.msn.com`).
  3. Efetua um Forward DNS (`socket.gethostbyname`) usando o hostname retornado, confirmando que o IP de destino corresponde exatamente ao IP original do cliente.
- **Cache Temporal de DNS**: Para evitar consultas excessivas aos servidores de DNS:
  - Ips validados com sucesso são marcados em cache interno por 24 horas (`86400` segundos).
  - Ips que falhem na verificação são bloqueados/cacheados por 1 hora (`3600` segundos).

---

## 3. Segurança, Decorators e Trava de Dispositivo Único

### `aluno_required(f)`
- **Tipo**: Decorator de Rota.
- **Regra**: Limita o acesso de rotas exclusivamente a usuários devidamente autenticados que possuam o papel (`role`) de `'aluno'`. Usuários em desconformidade são direcionados para o painel de login.

### `premium_required(f)`
- **Tipo**: Decorator de Rota.
- **Regra**: No modelo atual de software livre, todo usuário autenticado possui acesso premium. Por isso, o decorator é um alias direto de `aluno_required(f)` — apenas exige login de aluno.

> [!NOTE]
> O decorator `admin_required(f)` migrou para `rotas/admin.py` junto com a separação de ambientes Admin/Aluno (ver `docs/rotas/admin.md`). O `utils.py` permanece compartilhado entre os dois apps, mas contém apenas utilidades do aluno e da camada de dados.

## 4. Gamificação e Engajamento

### `calcular_ofensiva_usuario(user_id)`
- **Propósito**: Algoritmo de cálculo de ofensiva (Streak - dias consecutivos de estudos).
- **Lógica**: 
  1. Busca o histórico de respostas do usuário ordenado por data descendente.
  2. Converte os timestamps originais em UTC para a data correspondente do fuso horário brasileiro (UTC-3).
  3. Agrupa e elimina duplicidades de datas (o aluno respondeu várias questões no mesmo dia).
  4. Inicia uma contagem a partir de hoje (ou de ontem se hoje ainda não foi respondido) e verifica a existência de registros sequenciais decrescentes de 1 em 1 dia.
  5. Retorna o total de dias ininterruptos obtidos.

---

## 5. Higienização de Dados

### `slugify(text)`
- **Propósito**: Higieniza strings para inclusão segura de caminhos em URLs de SEO.
- **Ações**: Normaliza caracteres Unicode para desmembrar acentuações (`NFD`), converte todas as letras para minúsculas, exclui pontuações e substitui múltiplos espaços ou caracteres inválidos por hifens.
