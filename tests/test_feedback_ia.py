import os
import sys
import unittest
from unittest.mock import patch

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configura o ambiente de testes
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'teste-chave-secreta-feedback-ia')

from app import app
from escrita_global import ErroEscritaGlobal


class TestFeedbackQuestao(unittest.TestCase):
    """Reporte de erro na questão (/api/feedback) — gravação via Edge Function."""

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
    @patch('rotas.questao.escrever_global')
    def test_envio_valido_grava_feedback(self, mock_escrever, mock_questao_user, mock_utils_user):
        self._usuario_logado(mock_questao_user, mock_utils_user)

        response = self.client.post('/api/feedback', json={
            'id_questao': '500',
            'tipo_erro': 'Gabarito Errado',
            'descricao': 'A alternativa correta deveria ser a B.'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['success'])
        mock_escrever.assert_called_once_with(
            'feedback_question',
            id_questao=500,
            tipo_erro='Gabarito Errado',
            descricao='A alternativa correta deveria ser a B.'
        )

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.escrever_global')
    def test_tipo_invalido_retorna_400(self, mock_escrever, mock_questao_user, mock_utils_user):
        self._usuario_logado(mock_questao_user, mock_utils_user)

        response = self.client.post('/api/feedback', json={
            'id_questao': 500,
            'tipo_erro': 'Tipo fora do catálogo',
            'descricao': ''
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()['success'])
        mock_escrever.assert_not_called()

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.escrever_global')
    def test_id_invalido_retorna_400(self, mock_escrever, mock_questao_user, mock_utils_user):
        self._usuario_logado(mock_questao_user, mock_utils_user)

        response = self.client.post('/api/feedback', json={
            'id_questao': 'abc',
            'tipo_erro': 'Outro',
            'descricao': 'Teste'
        })

        self.assertEqual(response.status_code, 400)
        mock_escrever.assert_not_called()

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.escrever_global', side_effect=ErroEscritaGlobal(
        'Você atingiu o limite de envios. Tente novamente em 5 min.', 429
    ))
    def test_rate_limit_retorna_mensagem_amigavel(self, mock_escrever, mock_questao_user, mock_utils_user):
        self._usuario_logado(mock_questao_user, mock_utils_user)

        response = self.client.post('/api/feedback', json={
            'id_questao': 500,
            'tipo_erro': 'Outro',
            'descricao': 'Teste'
        })

        self.assertEqual(response.status_code, 429)
        self.assertIn('limite de envios', response.get_json()['error'])


class TestFeedbackIA(unittest.TestCase):
    """Reporte anônimo de problema em respostas da IA (/api/feedback_ia) —
    explicações, resumos e flashcards gerados. O relato vai para a triagem
    humana do painel admin (tabela feedbacks_ia), via Edge Function."""

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
    @patch('rotas.questao.escrever_global')
    def test_envio_valido_grava_relato(self, mock_escrever, mock_questao_user, mock_utils_user):
        """Envio válido encaminha id_questao/tipo/motivo/relato."""
        self._usuario_logado(mock_questao_user, mock_utils_user)

        response = self.client.post('/api/feedback_ia', json={
            'id_questao': 500,
            'tipo': 'explicacao',
            'motivo': 'citacao_legal',
            'relato': 'Citou o artigo errado.'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['success'])
        mock_escrever.assert_called_once_with(
            'feedback_ai',
            id_questao=500,
            tipo='explicacao',
            motivo='citacao_legal',
            relato='Citou o artigo errado.'
        )

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.escrever_global')
    def test_tipo_invalido_retorna_400(self, mock_escrever, mock_questao_user, mock_utils_user):
        self._usuario_logado(mock_questao_user, mock_utils_user)

        response = self.client.post('/api/feedback_ia', json={
            'id_questao': 500, 'tipo': 'video', 'motivo': 'outro'
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()['success'])
        mock_escrever.assert_not_called()

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.escrever_global')
    def test_motivo_invalido_retorna_400(self, mock_escrever, mock_questao_user, mock_utils_user):
        self._usuario_logado(mock_questao_user, mock_utils_user)

        response = self.client.post('/api/feedback_ia', json={
            'id_questao': 500, 'tipo': 'resumo', 'motivo': 'motivo_fora_do_catalogo'
        })

        self.assertEqual(response.status_code, 400)
        mock_escrever.assert_not_called()

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.escrever_global')
    def test_blocklist_bloqueia_relato_improprio(self, mock_escrever, mock_questao_user, mock_utils_user):
        """Mesma blocklist local dos comentários — sem moderação por IA."""
        self._usuario_logado(mock_questao_user, mock_utils_user)

        response = self.client.post('/api/feedback_ia', json={
            'id_questao': 500, 'tipo': 'flashcard', 'motivo': 'outro',
            'relato': 'isso é uma merda'
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()['success'])
        mock_escrever.assert_not_called()

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.escrever_global')
    def test_relato_longo_e_truncado_em_1000(self, mock_escrever, mock_questao_user, mock_utils_user):
        self._usuario_logado(mock_questao_user, mock_utils_user)

        response = self.client.post('/api/feedback_ia', json={
            'id_questao': 500, 'tipo': 'resumo', 'motivo': 'outro',
            'relato': 'a' * 2000
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_escrever.call_args.kwargs['relato'], 'a' * 1000)

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.escrever_global', side_effect=ErroEscritaGlobal(
        'Não foi possível salvar o feedback no momento.', 503
    ))
    def test_falha_da_edge_retorna_erro_controlado(self, mock_escrever, mock_questao_user, mock_utils_user):
        self._usuario_logado(mock_questao_user, mock_utils_user)

        response = self.client.post('/api/feedback_ia', json={
            'id_questao': 500, 'tipo': 'explicacao', 'motivo': 'outro'
        })

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.get_json()['error'],
            'Não foi possível salvar o feedback no momento.'
        )


if __name__ == '__main__':
    unittest.main()
