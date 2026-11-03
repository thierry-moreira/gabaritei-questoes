import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ['FLASK_ENV'] = 'development'
os.environ.setdefault('FLASK_SECRET_KEY', 'teste-chave-secreta-seguranca')

from app import app


class TestCSP(unittest.TestCase):
    """Regressão das diretivas de CSP endurecidas no F-11."""

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_diretivas_de_endurecimento_presentes(self):
        resposta = self.client.get('/aluno/login')
        csp = resposta.headers.get('Content-Security-Policy', '')

        self.assertIn("object-src 'none'", csp)
        self.assertIn("base-uri 'self'", csp)
        self.assertIn("frame-ancestors 'self'", csp)
        self.assertIn("form-action 'self'", csp)
        self.assertIn("default-src 'self'", csp)


if __name__ == '__main__':
    unittest.main()
