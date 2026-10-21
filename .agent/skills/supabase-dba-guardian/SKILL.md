# Skill: Supabase DBA Guardian - Gabaritei
Description: Protege a integridade do banco de dados Supabase e garante que todas as alterações de esquema sigam as melhores práticas de performance (índices, chaves estrangeiras) e segurança (RLS).

## Instructions
1. **Uso Exclusivo de Migrations:** NUNCA execute alterações de esquema (`CREATE`, `ALTER`, `DROP`) diretamente no banco de produção. Sempre crie um novo arquivo de migração local do Supabase (`supabase migration new <nome>`).
2. **Performance e Indexação Automática:** Sempre que criar ou alterar uma tabela, avalie a necessidade de índices. 
   - **Chaves Estrangeiras:** OBRIGATÓRIO criar um índice para toda coluna que for uma `FOREIGN KEY`.
   - **Filtros Frequentes:** OBRIGATÓRIO criar índices B-Tree para colunas muito usadas em filtros no painel de questões (ex: `banca`, `ano`, `materia_id`, `orgao`).
   - **Busca de Texto:** Se criar colunas para o "Texto de Apoio" ou "Enunciado" das questões, sugira a criação de índices GIN para busca textual rápida.
3. **Segurança por Padrão:** Toda nova tabela criada DEVE ter o Row Level Security (RLS) ativado por padrão (`ALTER TABLE <nome> ENABLE ROW LEVEL SECURITY;`).
4. **Validação de Segurança:** Antes de aplicar qualquer migração com `supabase db push`, você deve OBRIGATORIAMENTE executar o script `check_sql_safety.py` na pasta de migrações.

## Constraints
- **PROIBIDO DELETAR TABELAS:** NUNCA escreva ou execute comandos `DROP TABLE` sem confirmação explícita do usuário.
- **PROIBIDO DELETAR COLUNAS:** NUNCA execute `ALTER TABLE ... DROP COLUMN` em produção. Prefira renomear ou marcar a coluna como obsoleta.
- **NUNCA** desative o RLS (Row Level Security) do Supabase.