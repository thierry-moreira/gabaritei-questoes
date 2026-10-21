import os
import sys
import unittest

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configura o ambiente de testes
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'teste-chave-secreta-provisoria')

# Importa a aplicação Flask oficial
from app import app

class TestRotasFlask(unittest.TestCase):
    
    def setUp(self):
        """Inicializa o cliente de testes do Flask antes de cada teste."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    # -------------------------------------------------------------------------
    # Testes de Honeypots de Segurança
    # -------------------------------------------------------------------------
    def test_admin_honeypots(self):
        """Garante que as rotas administrativas padrão barrem requisições com 404 (Honeypot)."""
        endpoints = ['/admin', '/admin/', '/admin/login']
        for rota in endpoints:
            with self.subTest(rota=rota):
                response = self.client.get(rota)
                self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
