import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configura o ambiente de testes
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'teste-chave-secreta-feedback-ia')

from app import app


class TestFeedbackIA(unittest.TestCase):
    """Reporte anônimo de problema em respostas da IA (/api/feedback_ia) —
    explicações, resumos e flashcards gerados. O relato vai para a triagem
    humana do painel admin (tabela feedbacks_ia)."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def _usuario_logado(self, *mocks):
        for mock_user in mocks:
            mock_user.is_authenticated = True
            mock_user.id = '12345'
            mock_user.role = 'aluno'

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.safe_execute')
    @patch('rotas.questao.supabase')
    def test_envio_valido_grava_relato(self, mock_supabase, mock_safe_execute, mock_questao_user, mock_utils_user):
        """Envio válido grava id_questao/tipo/motivo/relato em feedbacks_ia."""
        self._usuario_logado(mock_questao_user, mock_utils_user)
        mock_safe_execute.return_value = MagicMock()

        response = self.client.post('/api/feedback_ia', json={
            'id_questao': 500,
            'tipo': 'explicacao',
            'motivo': 'citacao_legal',
            'relato': 'Citou o artigo errado.'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['success'])
        payload = mock_supabase.table.return_value.insert.call_args.args[0]
        self.assertEqual(payload['id_questao'], 500)
        self.assertEqual(payload['tipo'], 'explicacao')
        self.assertEqual(payload['motivo'], 'citacao_legal')
        self.assertEqual(payload['relato'], 'Citou o artigo errado.')

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.safe_execute')
    @patch('rotas.questao.supabase')
    def test_tipo_invalido_retorna_400(self, mock_supabase, mock_safe_execute, mock_questao_user, mock_utils_user):
        self._usuario_logado(mock_questao_user, mock_utils_user)

        response = self.client.post('/api/feedback_ia', json={
            'id_questao': 500, 'tipo': 'video', 'motivo': 'outro'
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()['success'])
        mock_supabase.table.return_value.insert.assert_not_called()

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.safe_execute')
    @patch('rotas.questao.supabase')
    def test_motivo_invalido_retorna_400(self, mock_supabase, mock_safe_execute, mock_questao_user, mock_utils_user):
        self._usuario_logado(mock_questao_user, mock_utils_user)

        response = self.client.post('/api/feedback_ia', json={
            'id_questao': 500, 'tipo': 'resumo', 'motivo': 'motivo_fora_do_catalogo'
        })

        self.assertEqual(response.status_code, 400)
        mock_supabase.table.return_value.insert.assert_not_called()

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.safe_execute')
    @patch('rotas.questao.supabase')
    def test_blocklist_bloqueia_relato_improprio(self, mock_supabase, mock_safe_execute, mock_questao_user, mock_utils_user):
        """Mesma blocklist local dos comentários — sem moderação por IA."""
        self._usuario_logado(mock_questao_user, mock_utils_user)

        response = self.client.post('/api/feedback_ia', json={
            'id_questao': 500, 'tipo': 'flashcard', 'motivo': 'outro',
            'relato': 'isso é uma merda'
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()['success'])
        mock_supabase.table.return_value.insert.assert_not_called()

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.safe_execute')
    @patch('rotas.questao.supabase')
    def test_relato_longo_e_truncado_em_1000(self, mock_supabase, mock_safe_execute, mock_questao_user, mock_utils_user):
        self._usuario_logado(mock_questao_user, mock_utils_user)
        mock_safe_execute.return_value = MagicMock()

        response = self.client.post('/api/feedback_ia', json={
            'id_questao': 500, 'tipo': 'resumo', 'motivo': 'outro',
            'relato': 'a' * 2000
        })

        self.assertEqual(response.status_code, 200)
        payload = mock_supabase.table.return_value.insert.call_args.args[0]
        self.assertEqual(len(payload['relato']), 1000)


if __name__ == '__main__':
    unittest.main()
