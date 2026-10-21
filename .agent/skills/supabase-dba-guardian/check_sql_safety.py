import os
import sys
import glob
import re

# Caminho para a pasta de migrações do Supabase
# Ajuste se a sua pasta for diferente de supabase/migrations
MIGRATIONS_DIR = os.path.join(os.getcwd(), 'supabase', 'migrations')

DANGEROUS_COMMANDS = [
    (r'\bDROP\s+TABLE\b', "A migração tenta DELETAR UMA TABELA INTEIRA."),
    (r'\bDROP\s+COLUMN\b', "A migração tenta DELETAR UMA COLUNA."),
    (r'\bTRUNCATE\b', "A migração tenta LIMPAR TODOS OS DADOS de uma tabela."),
    (r'\bDISABLE\s+ROW\s+LEVEL\s+SECURITY\b', "A migração tenta DESATIVAR A SEGURANÇA (RLS).")
]

def check_migrations():
    if not os.path.exists(MIGRATIONS_DIR):
        print(f"⚠️ Pasta de migrações não encontrada em: {MIGRATIONS_DIR}")
        print("Certifique-se de que está usando o fluxo correto do Supabase.")
        sys.exit(0)

    sql_files = glob.glob(os.path.join(MIGRATIONS_DIR, '*.sql'))
    if not sql_files:
        print("Nenhum arquivo .sql encontrado para verificar.")
        sys.exit(0)

    # Verifica apenas o arquivo mais recente (a migração atual)
    latest_file = max(sql_files, key=os.path.getctime)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        content = f.read().upper()
        
        for pattern, warning in DANGEROUS_COMMANDS:
            if re.search(pattern, content):
                print(f"❌ ALERTA CRÍTICO DE BANCO DE DADOS no arquivo {os.path.basename(latest_file)}")
                print(f"Motivo: {warning}")
                print("Ação Bloqueada: O Antigravity foi impedido de aplicar esta migração.")
                print("Se você realmente deseja fazer isso, execute a migração manualmente.")
                sys.exit(1)

    print("✅ Migração validada. Nenhum comando destrutivo crítico encontrado.")
    print("🚀 Otimizações e regras de segurança (RLS/Índices) devem estar presentes.")
    sys.exit(0)

if __name__ == "__main__":
    check_migrations()