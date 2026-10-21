import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configura o ambiente de testes
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'teste-chave-secreta-conta')

from app import app

class TestContaBlueprint(unittest.TestCase):

    def setUp(self):
        """Inicializa o cliente de testes do Flask antes de cada teste."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def _mock_aluno(self):
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_user.username = 'alunoteste'
        mock_user.email = 'aluno@gabaritei.com'
        return mock_user

    # -------------------------------------------------------------------------
    # Visualizacao e Atualizacao (sem senha)
    # -------------------------------------------------------------------------
    @patch('flask_login.utils._get_user')
    def test_visualizar_configuracoes_conta(self, mock_get_user):
        """Garante que a tela de configuracoes carrega com sucesso para o aluno."""
        mock_get_user.return_value = self._mock_aluno()
        response = self.client.get('/aluno/conta')
        self.assertEqual(response.status_code, 200)

    @patch('rotas.conta.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_atualizar_dados_sucesso(self, mock_get_user, mock_safe_execute):
        """Garante que o aluno atualize username/e-mail diretamente, sem confirmacao de senha."""
        mock_get_user.return_value = self._mock_aluno()
        mock_update_res = MagicMock()
        mock_update_res.data = [{'id': 12345}]
        mock_safe_execute.return_value = mock_update_res

        response = self.client.post('/aluno/conta', data={
            'username': 'novonome',
            'email': 'novoemail@local.com'
        })
        self.assertEqual(response.status_code, 302)

        with self.client.session_transaction() as sess:
            flashes = sess.get('_flashes', [])
            self.assertTrue(any("atualizadas com sucesso" in msg[1] for msg in flashes))

    # -------------------------------------------------------------------------
    # Reset Completo de Dados de Estudo (apenas frase de confirmacao)
    # -------------------------------------------------------------------------
    @patch('flask_login.utils._get_user')
    def test_resetar_dados_confirmacao_incorreta(self, mock_get_user):
        """Garante que o reset seja rejeitado se a frase de confirmacao estiver incorreta."""
        mock_get_user.return_value = self._mock_aluno()

        response = self.client.post('/aluno/conta/resetar-dados', data={
            'texto_confirmacao_reset': 'RESETAR DADOS ERRADOS'
        })
        self.assertEqual(response.status_code, 302)

        with self.client.session_transaction() as sess:
            flashes = sess.get('_flashes', [])
            self.assertTrue(any("Confirmação incorreta" in msg[1] for msg in flashes))

    @patch('rotas.conta.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_resetar_dados_sucesso(self, mock_get_user, mock_safe_execute):
        """Garante a delecao em lote dos dados de estudo com a frase correta (sem senha)."""
        mock_get_user.return_value = self._mock_aluno()

        # 1 update de meta + 8 deletes
        mock_res = MagicMock()
        mock_res.data = [{'id': 12345}]
        mock_safe_execute.side_effect = [mock_res] * 9

        response = self.client.post('/aluno/conta/resetar-dados', data={
            'texto_confirmacao_reset': 'RESETAR MEUS DADOS'
        })
        self.assertEqual(response.status_code, 302)

        with self.client.session_transaction() as sess:
            flashes = sess.get('_flashes', [])
            self.assertTrue(any("dados de estudo foram redefinidos" in msg[1] for msg in flashes))

    # -------------------------------------------------------------------------
    # Exclusao Definitiva (apenas frase de confirmacao)
    # -------------------------------------------------------------------------
    @patch('flask_login.utils._get_user')
    def test_excluir_conta_confirmacao_incorreta(self, mock_get_user):
        """Recusa a exclusao se a frase EXCLUIR MINHA CONTA for digitada incorretamente."""
        mock_get_user.return_value = self._mock_aluno()

        response = self.client.post('/aluno/conta/excluir', data={
            'texto_confirmacao': 'DELETAR MINHA CONTA'
        })
        self.assertEqual(response.status_code, 302)

        with self.client.session_transaction() as sess:
            flashes = sess.get('_flashes', [])
            self.assertTrue(any("Confirmação incorreta" in msg[1] for msg in flashes))

    @patch('rotas.conta.logout_user')
    @patch('rotas.conta.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_excluir_conta_sucesso(self, mock_get_user, mock_safe_execute, mock_logout):
        """Valida que a exclusao remove o usuario e faz logout (sem senha)."""
        mock_get_user.return_value = self._mock_aluno()

        mock_res_db = MagicMock()
        mock_safe_execute.side_effect = [mock_res_db]

        response = self.client.post('/aluno/conta/excluir', data={
            'texto_confirmacao': 'EXCLUIR MINHA CONTA'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(response.location, ['/', 'http://localhost/'])

        mock_logout.assert_called_once()
        with self.client.session_transaction() as sess:
            flashes = sess.get('_flashes', [])
            self.assertTrue(any("excluída permanentemente" in msg[1] for msg in flashes))

if __name__ == '__main__':
    unittest.main()
