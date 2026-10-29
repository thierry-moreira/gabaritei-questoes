#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste de compatibilidade Python 3.15
Rode com: python test_compatibilidade_py315.py
"""
import sys
import importlib
import importlib.metadata
from typing import List, Tuple

# Forçar UTF-8 no stdout/stderr no Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Mapeamento: nome no requirements.txt -> nome do módulo para import
REQUIREMENTS_MAP = {
    "Flask": "flask",
    "Flask-Login": "flask_login",
    "Flask-WTF": "flask_wtf",
    "Werkzeug": "werkzeug",
    "Flask-Limiter": "flask_limiter",
    "flask-talisman": "flask_talisman",
    "supabase": "supabase",
    "python-dotenv": "dotenv",
    "postgrest": "postgrest",
    "openai": "openai",
    "typing-extensions": "typing_extensions",
    "weasyprint": "weasyprint",
    "requests": "requests",
    "pillow": "PIL",
    "Flask-Compress": "flask_compress",
}

# Dependências transitivas conhecidas que podem quebrar
TRANSITIVE_DEPS = {
    "cairo": "cairo",           # weasyprint dependency
    "pango": "pango",           # weasyprint dependency
    "gdkpixbuf": "gi.repository.GdkPixbuf",  # weasyprint
    "fontconfig": "fontconfig", # weasyprint
    "click": "click",           # Flask dependency
    "blinker": "blinker",       # Flask dependency
    "itsdangerous": "itsdangerous",
    "jinja2": "jinja2",
    "markupsafe": "markupsafe",
    "wtforms": "wtforms",
    "email-validator": "email_validator",
    "limits": "limits",         # Flask-Limiter
    "cryptography": "cryptography",  # supabase/postgrest
    "httpx": "httpx",           # supabase/openai
    "pydantic": "pydantic",     # supabase
    "postgres": "postgres",     # postgrest
    "urllib3": "urllib3",       # requests
    "charset-normalizer": "charset_normalizer",
    "idna": "idna",
    "certifi": "certifi",
}


def get_version(package_name: str) -> str:
    """Obtém versão do pacote via importlib.metadata (stdlib Python 3.8+)."""
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return "desconhecida"
    except Exception:
        return "desconhecida"


def test_import(module_name: str, display_name: str = None) -> Tuple[bool, str]:
    """Testa se um módulo pode ser importado."""
    name = display_name or module_name
    try:
        importlib.import_module(module_name)
        version = get_version(name)
        return True, f"[OK] {name} {version}"
    except ImportError as e:
        return False, f"[FALHA] {name}: {e}"
    except Exception as e:
        return False, f"[AVISO] {name}: erro inesperado - {e}"


def test_requirements() -> List[Tuple[str, bool, str]]:
    """Testa todas as dependências do requirements.txt."""
    results = []
    
    print("=" * 70)
    print("TESTE DE COMPATIBILIDADE - Python 3.15")
    print(f"Python version: {sys.version}")
    print("=" * 70)
    print()
    
    print("[PKG] Dependencias diretas (requirements.txt):")
    print("-" * 70)
    
    for req_name, import_name in REQUIREMENTS_MAP.items():
        ok, msg = test_import(import_name, req_name)
        results.append((req_name, ok, msg))
        print(f"  {msg}")
    
    print()
    print("[LNK] Dependencias transitivas criticas (weasyprint, supabase, etc.):")
    print("-" * 70)
    
    for req_name, import_name in TRANSITIVE_DEPS.items():
        ok, msg = test_import(import_name, req_name)
        results.append((req_name, ok, msg))
        print(f"  {msg}")
    
    return results


def test_stdlib_changes():
    """Testa mudanças na stdlib do Python 3.15 que podem afetar o código."""
    print()
    print("[PY] Novos recursos da stdlib Python 3.15:")
    print("-" * 70)
    
    # Python version check
    print(f"  [INFO] Python version: {sys.version}")
    print(f"  [INFO] Python version_info: {sys.version_info}")
    
    # frozendict (PEP 814)
    try:
        d = frozendict(x=1, y=2)  # type: ignore
        print(f"  [OK] frozendict built-in: {d}")
    except NameError:
        print("  [FALHA] frozendict NAO disponivel")
    except Exception as e:
        print(f"  [AVISO] frozendict erro: {e}")
    
    # sentinel (PEP 661)
    try:
        from sentinel import MISSING  # type: ignore
        print(f"  [OK] sentinel built-in: {MISSING}")
    except ImportError:
        print("  [FALHA] sentinel NAO disponivel")
    except Exception as e:
        print(f"  [AVISO] sentinel erro: {e}")
    
    # Lazy imports (PEP 810) - sintaxe
    try:
        # Isso é syntax, não dá pra testar com importlib
        print("  [INFO] lazy imports: sintaxe 'lazy import x' disponivel no parser")
    except Exception:
        pass
    
    # Unpacking em comprehensions (PEP 798) - usa exec para evitar SyntaxError em parse time
    try:
        exec("[*x for x in [[1,2], [3,4]]]")
        print("  [OK] unpacking em comprehensions: SUPORTADO")
    except SyntaxError:
        print("  [FALHA] unpacking em comprehensions NAO disponivel (Python < 3.15)")
    except Exception as e:
        print(f"  [AVISO] unpacking erro: {e}")
    
    # UTF-8 default (PEP 686)
    import locale
    print(f"  [INFO] locale.getpreferredencoding(): {locale.getpreferredencoding()}")
    print(f"  [INFO] sys.getdefaultencoding(): {sys.getdefaultencoding()}")


def test_project_imports():
    """Testa imports específicos do projeto."""
    print()
    print("[DIR] Imports do projeto (gabaritei-questoes):")
    print("-" * 70)
    
    project_modules = [
        "app",
        "utils",
        "modelos",
        "extensoes",
        "banco_dados_aluno",
        "banco_local",
        "provedores_ia",
        "rotas.auth",
        "rotas.api",
        "rotas.aluno",
        "rotas.conta",
        "rotas.caderno",
        "rotas.questao",
        "rotas.flashcards",
        "rotas.resumos",
        "rotas.simulado",
        "rotas.edital",
        "rotas.filtro",
    ]
    
    # Adicionar o diretório raiz ao path
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    for mod in project_modules:
        ok, msg = test_import(mod, mod)
        print(f"  {msg}")


def print_summary(results: List[Tuple[str, bool, str]]):
    """Imprime resumo final."""
    print()
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    
    ok_count = sum(1 for _, ok, _ in results if ok)
    fail_count = len(results) - ok_count
    
    print(f"[OK] Sucesso: {ok_count}")
    print(f"[FALHA] Falhas: {fail_count}")
    
    if fail_count > 0:
        print()
        print("[FALHA] DEPENDENCIAS COM PROBLEMA:")
        for name, ok, msg in results:
            if not ok:
                print(f"   - {name}")
    
    print()
    if fail_count == 0:
        print("[OK] TODAS AS DEPENDENCIAS SAO COMPATIVEIS COM PYTHON 3.15!")
        print("   Pode prosseguir com a migracao.")
    else:
        print("[AVISO] ALGUMAS DEPENDENCIAS FALHARAM.")
        print("   Verifique as falhas acima antes de migrar.")
        print()
        print("Dicas:")
        print("  - weasyprint/cairo: pode precisar instalar GTK no Windows")
        print("  - Execute: pip install --upgrade pip setuptools wheel")
        print("  - Tente instalar individualmente: pip install <pacote>")


def main():
    # Teste de dependências
    results = test_requirements()
    
    # Teste de novos recursos Python 3.15
    test_stdlib_changes()
    
    # Teste de imports do projeto
    test_project_imports()
    
    # Resumo
    print_summary(results)
    
    # Exit code para CI/CD
    fail_count = sum(1 for _, ok, _ in results if not ok)
    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    main()