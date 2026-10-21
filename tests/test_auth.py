import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configura o ambiente de testes
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'teste-chave-secreta-provisoria')

# Importa a aplicação Flask oficial
from app import app

class TestAuthFlask(unittest.TestCase):
    
    def setUp(self):
        """Inicializa o cliente de testes do Flask antes de cada teste."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    # -------------------------------------------------------------------------
    # Fluxo Desktop (sem senha): entrada automatica
    # -------------------------------------------------------------------------
    @patch('rotas.auth.current_user')
    @patch('rotas.auth.safe_execute')
    def test_login_sem_usuario_mostra_tela_de_criacao(self, mock_safe_execute, mock_current_user):
        """Sem usuario local, a entrada renderiza a tela de criar usuario (200)."""
        mock_current_user.is_authenticated = False
        mock_res = MagicMock()
        mock_res.data = []
        mock_safe_execute.return_value = mock_res

        response = self.client.get('/aluno/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'username', response.data.lower())

    @patch('rotas.auth.current_user')
    @patch('rotas.auth.safe_execute')
    def test_login_com_usuario_entra_direto(self, mock_safe_execute, mock_current_user):
        """Com usuario local existente, a entrada faz login automatico e redireciona ao painel."""
        mock_current_user.is_authenticated = False
        mock_res = MagicMock()
        mock_res.data = [{'id': 7, 'username': 'Aluno Local', 'role': 'aluno', 'email': 'a@a.com'}]
        mock_safe_execute.return_value = mock_res

        response = self.client.get('/aluno/login')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/aluno/painel', response.headers['Location'])

    @patch('rotas.auth.current_user')
    def test_login_ja_autenticado_redireciona(self, mock_current_user):
        """Usuario ja autenticado e redirecionado direto ao painel."""
        mock_current_user.is_authenticated = True
        mock_current_user.role = 'aluno'

        response = self.client.get('/aluno/login')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/aluno/painel', response.headers['Location'])


    # -------------------------------------------------------------------------
    # Criacao do usuario local (POST /aluno/criar)
    # -------------------------------------------------------------------------
    @patch('rotas.auth.current_user')
    @patch('rotas.auth.safe_execute')
    def test_criar_usuario_sucesso(self, mock_safe_execute, mock_current_user):
        """Primeiro acesso: cria o usuario e entra direto no painel."""
        mock_current_user.is_authenticated = False
        res_busca = MagicMock(); res_busca.data = []
        res_insert = MagicMock(); res_insert.data = [{'id': 42, 'username': 'Thierry', 'role': 'aluno'}]
        mock_safe_execute.side_effect = [res_busca, res_insert]

        response = self.client.post('/aluno/criar', data={'username': 'Thierry', 'email': 't@t.com'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/aluno/painel', response.headers['Location'])

        with self.client.session_transaction() as sess:
            flashes = sess.get('_flashes', [])
            self.assertTrue(any("Bem-vindo" in msg[1] for msg in flashes))

    @patch('rotas.auth.current_user')
    @patch('rotas.auth.safe_execute')
    def test_criar_usuario_sem_nome_bloqueado(self, mock_safe_execute, mock_current_user):
        """Sem username, volta para a entrada com flash de aviso."""
        mock_current_user.is_authenticated = False
        res_busca = MagicMock(); res_busca.data = []
        mock_safe_execute.return_value = res_busca

        response = self.client.post('/aluno/criar', data={'username': ''})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/aluno/login', response.headers['Location'])

        with self.client.session_transaction() as sess:
            flashes = sess.get('_flashes', [])
            self.assertTrue(any("Informe como quer ser chamado" in msg[1] for msg in flashes))

    @patch('rotas.auth.current_user')
    @patch('rotas.auth.safe_execute')
    def test_criar_usuario_com_conta_existente_entra_direto(self, mock_safe_execute, mock_current_user):
        """Se ja existe usuario local, o POST de criar apenas entra direto (sem duplicar)."""
        mock_current_user.is_authenticated = False
        res_busca = MagicMock(); res_busca.data = [{'id': 7, 'username': 'Aluno Local', 'role': 'aluno'}]
        mock_safe_execute.return_value = res_busca

        response = self.client.post('/aluno/criar', data={'username': 'Outro'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/aluno/painel', response.headers['Location'])
        self.assertEqual(mock_safe_execute.call_count, 1)

    def test_logout(self):
        """Garante que a rota de logout limpe a sessao do aluno e redirecione para a home."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['web_session_token'] = 'token_do_aluno'
                sess['admin_logged_in'] = True  # Mantem dados de admin protegidos
                
            response = c.get('/logout')
            self.assertEqual(response.status_code, 302)
            self.assertIn('/', response.headers['Location'])
            
            with c.session_transaction() as sess:
                self.assertNotIn('web_session_token', sess)
                self.assertTrue(sess.get('admin_logged_in'))

    # -------------------------------------------------------------------------
    # Rotas Removidas (Migracao Desktop) — devem responder 404/405
    # -------------------------------------------------------------------------
    def test_rotas_removidas_404(self):
        """Cadastro, recuperacao e verificacao de e-mail foram extintos."""
        removidas_get = ['/aluno/cadastro', '/esqueci-senha', '/redefinir-senha/token-falso',
                         '/verificar-email/1', '/reenviar-codigo/1']
        for rota in removidas_get:
            with self.subTest(rota=rota):
                self.assertEqual(self.client.get(rota).status_code, 404)
        # POST /aluno/login nao existe mais (login e automatico, apenas GET)
        self.assertEqual(self.client.post('/aluno/login', data={'email': 'x', 'password': 'y'}).status_code, 405)

if __name__ == '__main__':
    unittest.main()
