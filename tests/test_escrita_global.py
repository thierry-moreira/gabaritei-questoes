import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ.setdefault('FLASK_SECRET_KEY', 'teste-chave-secreta-escrita-global')

from escrita_global import ErroEscritaGlobal, escrever_global


class TestEscritaGlobal(unittest.TestCase):
    """Contrato HTTP da Edge Function secure-global-write."""

    @patch('escrita_global._ANON_KEY', 'anon-teste')
    @patch('escrita_global._SUPABASE_URL', 'https://teste.supabase.co/')
    @patch('escrita_global.requests.post')
    @patch('escrita_global._sessao_atual')
    def test_envia_payload_e_headers_do_aluno(self, mock_sessao, mock_post):
        mock_sessao.return_value = MagicMock(access_token='jwt-do-aluno')
        mock_post.return_value = MagicMock(status_code=200)

        escrever_global(
            'feedback_question',
            id_questao=500,
            tipo_erro='Outro',
            descricao='Teste',
        )

        args, kwargs = mock_post.call_args
        self.assertEqual(
            args[0],
            'https://teste.supabase.co/functions/v1/secure-global-write'
        )
        self.assertEqual(kwargs['json'], {
            'operation': 'feedback_question',
            'id_questao': 500,
            'tipo_erro': 'Outro',
            'descricao': 'Teste',
        })
        self.assertEqual(kwargs['headers']['Authorization'], 'Bearer jwt-do-aluno')
        self.assertEqual(kwargs['headers']['apikey'], 'anon-teste')

    @patch('escrita_global.requests.post')
    @patch('escrita_global._sessao_atual', return_value=None)
    def test_sem_sessao_falha_antes_de_chamar_a_edge(self, mock_sessao, mock_post):
        with self.assertRaises(ErroEscritaGlobal) as ctx:
            escrever_global('feedback_ai', id_questao=1)

        self.assertEqual(ctx.exception.status, 401)
        self.assertIn('sessão expirou', ctx.exception.mensagem)
        mock_post.assert_not_called()

    @patch('escrita_global._SUPABASE_URL', 'https://teste.supabase.co')
    @patch('escrita_global.requests.post')
    @patch('escrita_global._sessao_atual')
    def test_rate_limit_vira_mensagem_amigavel(self, mock_sessao, mock_post):
        import requests

        mock_sessao.return_value = MagicMock(access_token='jwt-do-aluno')
        resposta = MagicMock(status_code=429)
        resposta.json.return_value = {
            'code': 'rate_limited',
            'retry_after_seconds': 301,
        }
        mock_post.return_value = resposta

        with self.assertRaises(ErroEscritaGlobal) as ctx:
            escrever_global('feedback_question', id_questao=1)

        self.assertEqual(ctx.exception.status, 429)
        self.assertIn('6 min', ctx.exception.mensagem)

    @patch('escrita_global._SUPABASE_URL', 'https://teste.supabase.co')
    @patch('escrita_global.requests.post')
    @patch('escrita_global._sessao_atual')
    def test_erro_de_rede_vira_503(self, mock_sessao, mock_post):
        import requests

        mock_sessao.return_value = MagicMock(access_token='jwt-do-aluno')
        mock_post.side_effect = requests.ConnectionError('sem rede')

        with self.assertRaises(ErroEscritaGlobal) as ctx:
            escrever_global('feedback_question', id_questao=1)

        self.assertEqual(ctx.exception.status, 503)
        self.assertIn('conectar', ctx.exception.mensagem)

    @patch('escrita_global._SUPABASE_URL', 'https://teste.supabase.co')
    @patch('escrita_global.requests.post')
    @patch('escrita_global._sessao_atual')
    def test_payload_invalido_vira_400(self, mock_sessao, mock_post):
        mock_sessao.return_value = MagicMock(access_token='jwt-do-aluno')
        resposta = MagicMock(status_code=400)
        resposta.json.return_value = {'code': 'invalid_payload'}
        mock_post.return_value = resposta

        with self.assertRaises(ErroEscritaGlobal) as ctx:
            escrever_global('feedback_question', id_questao=1)

        self.assertEqual(ctx.exception.status, 400)
        self.assertIn('inválidos', ctx.exception.mensagem)


if __name__ == '__main__':
    unittest.main()
