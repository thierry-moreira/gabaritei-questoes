# Documentação Técnica: IA com BYOK (Bring Your Own Key)

## Visão Geral

O app do aluno **não tem chave de IA própria**: cada aluno usa a **própria chave de API** (OpenAI, Google Gemini ou Anthropic), configurada em **Configurações da conta → Inteligência Artificial**. O dev configura a dele pela própria UI, como qualquer aluno — a antiga `OPENAI_API_KEY` do `.env` não existe mais.

| Camada | Arquivo | Responsabilidade |
|---|---|---|
| Provedores | `provedores_ia.py` | Listas oficiais de modelos, dispatch por provedor, pings de validação, tradução de payload/imagens |
| Armazenamento local | `banco_local.py` | SQLite em `GABARITEI_LOCAL_DIR` com a chave cifrada via **DPAPI** |
| UI + endpoints | `rotas/conta.py` + `templates/aluno/conta.html` | Card de configuração, `POST /api/ia/config`, `POST /api/ia/config/remover` |
| Consumo | `rotas/questao.py` | `/api/ia_explica` e `/api/ia/gerar_estudo` chamam `chamar_ia()` |

## O que NÃO muda (congelado)

- **System prompts** byte a byte — continuam definidos nas rotas.
- `/api/ia_explica`: `temperature=0.0, top_p=0.1, presence_penalty=0.0, frequency_penalty=0.0`.
- `/api/ia/gerar_estudo`: `TEMPERATURE_GPT = 0.3`.
- Caches e persistência no Supabase intactos: `explicacoes_ia` (global por questão), `ia_cache_estudo` (global por questão+tipo), `resumos_estudo`/`flashcards` (por aluno).

## Modelos pré-configurados (`PROVEDORES`)

| Provedor | Modelos (nesta ordem) | Padrão pré-selecionado |
|---|---|---|
| **OpenAI** | `gpt-6.1-sol` · `gpt-5.6-luna` · `gpt-5.6-terra` · `gpt-6-sol` · `gpt-5.2-2025-12-11` · `gpt-5-2025-08-07` · `gpt-5.4-2026-03-05` | `gpt-5.6-luna` |
| **Google Gemini** | `gemini-4-argon` · `gemini-3.8-flash` · `gemini-3.1-pro-preview` · `gemini-3.5-flash-lite` | `gemini-4-argon` |
| **Anthropic Claude** | `claude-haiku-5-5` · `claude-sonnet-5-5` | `claude-sonnet-5-5` |

Além das listas, o aluno pode digitar um **modelo personalizado** (valores futuros mudam de ID rápido).

## Transporte por provedor

- **OpenAI**: SDK `openai` oficial; role `developer` (como sempre foi).
- **Google Gemini**: endpoint **OpenAI-compatível** do Google (`/v1beta/openai/`) — mesmo SDK, trocando apenas `base_url`; role convertida para `system`.
- **Anthropic**: Messages API **nativa** via `requests` (não existe compat OpenAI); `max_tokens=8192`; imagens são baixadas e convertidas para base64 (limite 8 MB; falha individual → gera sem a imagem, como o fluxo já tolera).

Parâmetros não suportados por um **provedor** são omitidos com log (ex.: `presence_penalty`/`frequency_penalty` não existem na Anthropic **nem no endpoint OpenAI-compat do Gemini** — que aceita apenas `temperature`/`top_p` e rejeita os penalties com 400 `Unknown name "frequency_penalty": Cannot find field`; ver `_PARAMETROS_SUPORTADOS`).

### Modelos de raciocínio (família gpt-5/6) e parâmetros de sampling

Os modelos de raciocínio da OpenAI (`gpt-5.6-luna`, `gpt-6.1-sol` etc.) **não aceitam parâmetros de sampling** — a API rejeita `temperature`/`top_p`/penalties com 400 `unsupported_value` ("Only the default (1) value is supported"). Nesses modelos o determinismo pedagógico não vem do `temperature`, e sim da própria cadeia de raciocínio — por isso a OpenAI os removeu.

**Como a camada lida:** os parâmetros calibrados são **sempre enviados na 1ª tentativa** (congelamento preservado); se o modelo rejeitar um deles (o erro traz o `param` exato), a camada o remove e **repete a chamada** (máx. 2 repetições) com o default do modelo. Modelos que aceitam sampling (família gpt-4o, antigos e futuros) continuam recebendo exatamente a configuração calibrada. O mesmo mecanismo defensivo cobre o caminho REST da Anthropic (`_param_rejeitado` + loop de tentativas).

## Segurança da chave

1. **Nunca no Supabase** — a chave só sai da máquina em direção ao próprio provedor escolhido.
2. **Nunca em plaintext em disco (Windows)** — o SQLite guarda um blob **DPAPI** (`CryptProtectData` via `ctypes`, sem dependências): só o mesmo usuário do Windows decifra. Fora do Windows: fallback base64 com aviso no log.
3. **Nunca em logs**; endpoints devolvem apenas a máscara (`sk-1…5555` via `mascarar_chave`).
4. **Por usuário logado** (`config_ia.id_usuario` é PK) — contas distintas na mesma máquina ficam isoladas.
5. Reset dos dados e exclusão da conta apagam também a config local (LGPD).

## "Salvar e testar" (validação sem custo)

`testar_chave()` faz 2 **GETs gratuitos**: listar `/models` e recuperar `/models/{modelo}` — valida chave **e** modelo sem gastar tokens. Erros mapeados: 401/403 → chave inválida; 404 → modelo inválido.

## Erros amigáveis (`ErroIA.codigo`)

`sem_config`, `chave_invalida`, `modelo_invalido`, `rate_limit`, `falha_rede`, `resposta_vazia`, `sem_credito`.

**Falta de crédito:** a Anthropic responde **402 `billing_error`** (a API não tem free tier — a chave exige créditos ativos no Console) e a OpenAI usa `429 insufficient_quota`. Ambos são traduzidos para uma mensagem clara ("Sua conta no provedor está sem créditos/billing ativo...") — tanto no "Salvar e testar" quanto na geração.

## Custos

Cada geração é cobrada na conta do próprio aluno no provedor. Os caches globais (`explicacoes_ia`, `ia_cache_estudo`) reduzem drasticamente o custo coletivo: a primeira geração de uma questão é paga por um aluno; todos os demais pegam do cache — **inclusive alunos sem chave configurada**. Os caches (global e do próprio caderno) são consultados **antes** do check de BYOK: sem chave, o aluno ainda recebe qualquer explicação/resumo/flashcard já presente no banco; apenas **gerações inéditas** exigem a chave (e respondem com mensagem tratada + atalho para Configurações da conta).
