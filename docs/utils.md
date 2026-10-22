# Documentação Técnica: `utils.py`

## Descrição Geral
O módulo `utils.py` é o núcleo de inteligência auxiliar, segurança e utilitários transversais do app do aluno. Ele reúne decorators de controle de rotas por perfis de acesso, tratativas de resiliência em banco de dados, filtros de moderação inteligente de texto e utilitários de gamificação.

---

## 1. Resiliência de Infraestrutura e Rede

### `safe_execute(query_func)`
- **Propósito**: Camada de resiliência sobre chamadas síncronas ao Supabase (PostgREST).
- **Lógica de Retentativa (Retry)**: Tenta executar a consulta fornecida até 3 vezes caso ocorra uma falha técnica momentânea de rede ou conexão.
- **Delay Exponencial**: Aplica uma pausa estática de `0.5` segundos entre tentativas malsucedidas.
- **Tratamento de Exceções**: Se a falha persistir após a terceira tentativa, o sistema registra um log de erro crítico (`logger.error`) detalhado e propaga o erro de forma visível para facilitar o diagnóstico de auditoria.

---

## 2. Segurança e Decorators de Rota

### `aluno_required(f)`
- **Tipo**: Decorator de Rota.
- **Regra**: Limita o acesso de rotas exclusivamente a usuários devidamente autenticados que possuam o papel (`role`) de `'aluno'`. Usuários em desconformidade são direcionados para o painel de login.

> [!NOTE]
> O decorator `admin_required(f)` migrou para `rotas/admin.py` junto com a separação de ambientes Admin/Aluno (ver `docs/rotas/admin.md` no repositório do painel administrativo). O `utils.py` deste app contém apenas utilidades do aluno e da camada de dados.

## 3. Gamificação e Engajamento

### `calcular_ofensiva_usuario(user_id)`
- **Propósito**: Algoritmo de cálculo de ofensiva (Streak - dias consecutivos de estudos).
- **Lógica**: 
  1. Busca o histórico de respostas do usuário ordenado por data descendente.
  2. Converte os timestamps originais em UTC para a data correspondente do fuso horário brasileiro (UTC-3).
  3. Agrupa e elimina duplicidades de datas (o aluno respondeu várias questões no mesmo dia).
  4. Inicia uma contagem a partir de hoje (ou de ontem se hoje ainda não foi respondido) e verifica a existência de registros sequenciais decrescentes de 1 em 1 dia.
  5. Retorna o total de dias ininterruptos obtidos.

---

## 4. Higienização de Dados

### `slugify(text)`
- **Propósito**: Higieniza strings para inclusão segura de caminhos em URLs de SEO.
- **Ações**: Normaliza caracteres Unicode para desmembrar acentuações (`NFD`), converte todas as letras para minúsculas, exclui pontuações e substitui múltiplos espaços ou caracteres inválidos por hifens.
