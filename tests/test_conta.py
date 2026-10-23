import os
import sys
import tempfile
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
        # Banco local (BYOK — chave de IA) isolado em tmpdir: os testes jamais
        # devem tocar o AppData real do desenvolvedor.
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ['GABARITEI_LOCAL_DIR'] = self._tmpdir.name

    def tearDown(self):
        self._tmpdir.cleanup()
        os.environ.pop('GABARITEI_LOCAL_DIR', None)

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

        # 1 update de meta + 12 deletes (novos: progresso de editais e reports
        # de comentários — ambos com dono)
        mock_res = MagicMock()
        mock_res.data = [{'id': 12345}]
        mock_safe_execute.side_effect = [mock_res] * 13

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
        # 2 writes: delete de reports_comentarios + delete de usuarios
        mock_safe_execute.side_effect = [mock_res_db, mock_res_db]

        response = self.client.post('/aluno/conta/excluir', data={
            'texto_confirmacao': 'EXCLUIR MINHA CONTA'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(response.location, ['/', 'http://localhost/'])

        mock_logout.assert_called_once()
        with self.client.session_transaction() as sess:
            flashes = sess.get('_flashes', [])
            self.assertTrue(any("excluída permanentemente" in msg[1] for msg in flashes))

    # -------------------------------------------------------------------------
    # Card de IA na tela de conta (renderização do BYOK)
    # -------------------------------------------------------------------------
    @patch('flask_login.utils._get_user')
    def test_visualizar_conta_contem_card_ia(self, mock_get_user):
        """A tela de configurações exibe o card 'Inteligência Artificial'."""
        mock_get_user.return_value = self._mock_aluno()
        response = self.client.get('/aluno/conta')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Inteligência Artificial', html)
        self.assertIn('SUA CHAVE, SEU CONTROLE', html)

    # -------------------------------------------------------------------------
    # Configuração de IA — BYOK (/api/ia/config e /api/ia/config/remover)
    # -------------------------------------------------------------------------
    @patch('rotas.conta.testar_chave', return_value=(False, 'Chave de API inválida.'))
    @patch('flask_login.utils._get_user')
    def test_config_ia_provedor_nao_suportado(self, mock_get_user, mock_testar):
        """Rejeita provedores fora da lista oficial (openai/gemini/anthropic)."""
        mock_get_user.return_value = self._mock_aluno()
        response = self.client.post('/api/ia/config', json={
            'provedor': 'deepseek', 'modelo': 'x', 'chave': 'a' * 40
        })
        self.assertEqual(response.status_code, 400)
        mock_testar.assert_not_called()

    @patch('rotas.conta.testar_chave')
    @patch('flask_login.utils._get_user')
    def test_config_ia_chave_curta(self, mock_get_user, mock_testar):
        """Rejeita chaves absurdamente curtas antes de qualquer rede."""
        mock_get_user.return_value = self._mock_aluno()
        response = self.client.post('/api/ia/config', json={
            'provedor': 'openai', 'modelo': 'gpt-5.6-luna', 'chave': 'curta'
        })
        self.assertEqual(response.status_code, 400)
        mock_testar.assert_not_called()

    @patch('rotas.conta.testar_chave', return_value=(False, 'Chave de API inválida.'))
    @patch('flask_login.utils._get_user')
    def test_config_ia_ping_falha(self, mock_get_user, mock_testar):
        """Chave rejeitada pelo provedor não é salva (400 + motivo)."""
        mock_get_user.return_value = self._mock_aluno()
        response = self.client.post('/api/ia/config', json={
            'provedor': 'openai', 'modelo': 'gpt-5.6-luna', 'chave': 'sk-' + '1' * 40
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json().get('error'), 'Chave de API inválida.')

    @patch('rotas.conta.ler_config_ia')
    @patch('rotas.conta.salvar_config_ia')
    @patch('rotas.conta.testar_chave', return_value=(True, ''))
    @patch('flask_login.utils._get_user')
    def test_config_ia_sucesso_sem_vazamento(self, mock_get_user, mock_testar, mock_salvar, mock_ler):
        """Salva a config localmente e a resposta SÓ contém a máscara da chave."""
        CHAVE = 'sk-11112222333344445555'
        mock_get_user.return_value = self._mock_aluno()
        mock_ler.return_value = {'provedor': 'openai', 'modelo': 'gpt-5.6-luna', 'chave': CHAVE}
        response = self.client.post('/api/ia/config', json={
            'provedor': 'openai', 'modelo': 'gpt-5.6-luna', 'chave': CHAVE
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json().get('success'))
        mock_salvar.assert_called_once()
        corpo = response.get_data(as_text=True)
        self.assertNotIn(CHAVE, corpo)          # chave completa: NUNCA
        # get_json decodifica os escapes do jsonify (\u2026 → …)
        self.assertEqual(response.get_json()['status']['mascara'], 'sk-1…5555')

    @patch('rotas.conta.remover_config_ia', return_value=True)
    @patch('flask_login.utils._get_user')
    def test_remover_config_ia(self, mock_get_user, mock_remover):
        """Endpoint de remoção da chave local (LGPD)."""
        mock_get_user.return_value = self._mock_aluno()
        response = self.client.post('/api/ia/config/remover')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json().get('success'))
        mock_remover.assert_called_once()

if __name__ == '__main__':
    unittest.main()
