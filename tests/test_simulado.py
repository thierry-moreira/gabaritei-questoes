import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configura o ambiente de testes
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'teste-chave-secreta-simulado')

from app import app


class TestSimuladoPrivacidadeF04(unittest.TestCase):
    """F-04: simulado privado de outro aluno não vaza gabarito/ranking/PDF.

    O guard único `_simulado_do_usuario_ou_none` é exercitado pelas rotas
    reais; os mocks simulam o RLS owner-only da tabela `simulados` e a view
    pública (que não devolve o privado alheio).
    """

    ID_SIMULADO = '10955679-f9c8-4e55-b971-7bd0ff00bd99'
    ID_ALUNO = 12345

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['LOGIN_DISABLED'] = True  # Ignora @login_required do Flask-Login
        self.client = app.test_client()

    def _autenticar_aluno(self, mock_get_user):
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = self.ID_ALUNO
        mock_user.username = 'aluno_teste'
        mock_user.tema = 'light'
        mock_get_user.return_value = mock_user
        return mock_user

    def _mocks_por_tabela(self, mock_supabase, nomes):
        mocks = {nome: MagicMock() for nome in nomes}
        mock_supabase.table.side_effect = lambda nome: mocks[nome]
        return mocks

    def _sem_acesso(self, mock_safe_execute):
        """RLS esconde o privado alheio; a view pública também não o retorna."""
        mock_safe_execute.side_effect = [
            MagicMock(data=[]),  # tabela simulados (owner-only)
            MagicMock(data=[]),  # view_simulados_publicos (só eh_privado=false)
        ]

    def _simulado_proprio_privado(self):
        return {
            'id': self.ID_SIMULADO,
            'titulo': 'Meu simulado privado',
            'descricao': 'Conteúdo privado',
            'eh_privado': True,
            'id_criador': self.ID_ALUNO,
        }

    def _simulado_publico_alheio(self):
        return {
            'id': self.ID_SIMULADO,
            'titulo': 'Simulado público de outro aluno',
            'descricao': 'Conteúdo público',
            'eh_meu': False,
        }

    # -------------------------------------------------------------------------
    # Privado alheio: redirect e nenhuma consulta de questões/gabarito/ranking
    # -------------------------------------------------------------------------

    @patch('rotas.simulado.supabase')
    @patch('rotas.simulado.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_fazer_simulado_privado_alheio_nao_consulta_questoes(
        self, mock_get_user, mock_safe_execute, mock_supabase
    ):
        self._autenticar_aluno(mock_get_user)
        self._sem_acesso(mock_safe_execute)

        response = self.client.get(f'/aluno/simulados/fazer/{self.ID_SIMULADO}')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/aluno/simulados', response.headers['Location'])
        self.assertEqual(
            [c.args[0] for c in mock_supabase.table.call_args_list],
            ['simulados', 'view_simulados_publicos'],
        )
        mock_supabase.rpc.assert_not_called()

    @patch('rotas.simulado.supabase')
    @patch('rotas.simulado.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_corrigir_simulado_privado_alheio_nao_carrega_gabarito_nem_grava(
        self, mock_get_user, mock_safe_execute, mock_supabase
    ):
        self._autenticar_aluno(mock_get_user)
        self._sem_acesso(mock_safe_execute)

        response = self.client.post(f'/aluno/simulados/corrigir/{self.ID_SIMULADO}')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/aluno/simulados', response.headers['Location'])
        self.assertEqual(
            [c.args[0] for c in mock_supabase.table.call_args_list],
            ['simulados', 'view_simulados_publicos'],
        )
        # Nenhum gabarito foi consultado, nenhum resultado foi inserido e a
        # RPC de ranking não foi chamada.
        self.assertNotIn('alternativas_questao',
                         [c.args[0] for c in mock_supabase.table.call_args_list])
        self.assertNotIn('simulados_resultados',
                         [c.args[0] for c in mock_supabase.table.call_args_list])
        mock_supabase.rpc.assert_not_called()

    @patch('rotas.simulado.supabase')
    @patch('rotas.simulado.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_ranking_simulado_privado_alheio_nao_chama_rpc(
        self, mock_get_user, mock_safe_execute, mock_supabase
    ):
        self._autenticar_aluno(mock_get_user)
        self._sem_acesso(mock_safe_execute)

        response = self.client.get(f'/aluno/simulados/ranking/{self.ID_SIMULADO}')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/aluno/simulados', response.headers['Location'])
        self.assertEqual(
            [c.args[0] for c in mock_supabase.table.call_args_list],
            ['simulados', 'view_simulados_publicos'],
        )
        mock_supabase.rpc.assert_not_called()

    @patch('rotas.simulado.supabase')
    @patch('rotas.simulado.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_ranking_privado_alheio_bloqueia_mesmo_se_consulta_devolver_linha(
        self, mock_get_user, mock_safe_execute, mock_supabase
    ):
        """F-05: a checagem explícita de dono bloqueia antes da RPC/ranking."""
        self._autenticar_aluno(mock_get_user)
        self._mocks_por_tabela(
            mock_supabase, ('simulados', 'view_simulados_publicos')
        )
        # Simula falha/configuração futura de RLS que exponha a linha privada.
        mock_safe_execute.return_value = MagicMock(data=[{
            'id': self.ID_SIMULADO,
            'titulo': 'Privado de outro aluno',
            'eh_privado': True,
            'id_criador': self.ID_ALUNO + 1,
        }])

        response = self.client.get(f'/aluno/simulados/ranking/{self.ID_SIMULADO}')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/aluno/simulados', response.headers['Location'])
        self.assertEqual(
            [c.args[0] for c in mock_supabase.table.call_args_list],
            ['simulados'],
        )
        mock_supabase.rpc.assert_not_called()

    @patch('rotas.simulado.supabase')
    @patch('rotas.simulado.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_pdf_simulado_privado_alheio_nao_consulta_questoes(
        self, mock_get_user, mock_safe_execute, mock_supabase
    ):
        self._autenticar_aluno(mock_get_user)
        self._sem_acesso(mock_safe_execute)

        response = self.client.get(f'/simulado/{self.ID_SIMULADO}/pdf')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/aluno/simulados', response.headers['Location'])
        self.assertEqual(
            [c.args[0] for c in mock_supabase.table.call_args_list],
            ['simulados', 'view_simulados_publicos'],
        )
        self.assertNotIn('view_questoes_completa',
                         [c.args[0] for c in mock_supabase.table.call_args_list])
        self.assertNotIn('alternativas_questao',
                         [c.args[0] for c in mock_supabase.table.call_args_list])

    @patch('rotas.simulado.supabase')
    @patch('rotas.simulado.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_pdf_simulado_privado_alheio_bloqueia_mesmo_se_busca_devolver_linha(
        self, mock_get_user, mock_safe_execute, mock_supabase
    ):
        """F-06 (defesa em profundidade): mesmo que a consulta à tabela
        `simulados` devolvesse a linha privada de outro aluno (por exemplo,
        com a RLS mal configurada), a checagem explícita de
        `eh_privado`/`id_criador` bloqueia antes de carregar questões,
        alternativas e gabarito.
        """
        self._autenticar_aluno(mock_get_user)
        mocks = self._mocks_por_tabela(
            mock_supabase, ('simulados', 'view_simulados_publicos')
        )
        mock_safe_execute.return_value = MagicMock(data=[{
            'id': self.ID_SIMULADO,
            'titulo': 'Privado de outro aluno',
            'eh_privado': True,
            'id_criador': self.ID_ALUNO + 1,
        }])

        response = self.client.get(f'/simulado/{self.ID_SIMULADO}/pdf')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/aluno/simulados', response.headers['Location'])
        self.assertEqual(
            [c.args[0] for c in mock_supabase.table.call_args_list],
            ['simulados'],
        )
        mocks['view_simulados_publicos'].select.assert_not_called()

    # -------------------------------------------------------------------------
    # Acessos permitidos: privado próprio e público alheio
    # -------------------------------------------------------------------------

    @patch('rotas.simulado.supabase')
    @patch('rotas.simulado.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_corrigir_simulado_privado_proprio_permite_e_grava_resultado(
        self, mock_get_user, mock_safe_execute, mock_supabase
    ):
        self._autenticar_aluno(mock_get_user)
        mocks = self._mocks_por_tabela(
            mock_supabase,
            ('simulados', 'view_simulados_publicos', 'simulados_questoes',
             'alternativas_questao', 'simulados_resultados'),
        )

        mock_safe_execute.side_effect = [
            MagicMock(data=[self._simulado_proprio_privado()]),  # simulados
            MagicMock(data=[{'id_questao': 10}]),                # simulado_questoes
            MagicMock(data=[{'id_questao': 10, 'letra': 'A'}]),  # gabarito
            MagicMock(data=[]),                                  # insert resultado
            MagicMock(data=[]),                                  # RPC ranking
        ]
        mock_supabase.rpc.return_value = MagicMock(data=[])

        response = self.client.post(
            f'/aluno/simulados/corrigir/{self.ID_SIMULADO}',
            data={'resp_10': 'A'},
        )

        self.assertEqual(response.status_code, 200)
        mocks['simulados_resultados'].insert.assert_called_once_with({
            'id_simulado': self.ID_SIMULADO,
            'id_usuario': self.ID_ALUNO,
            'nota': 10.0,
            'respostas_corretas': 1,
            'total_questoes': 1,
        })
        mock_supabase.rpc.assert_called_once_with(
            'ranking_simulado', {'p_id_simulado': self.ID_SIMULADO}
        )

    @patch('rotas.simulado.supabase')
    @patch('rotas.simulado.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_corrigir_simulado_publico_alheio_permite(
        self, mock_get_user, mock_safe_execute, mock_supabase
    ):
        self._autenticar_aluno(mock_get_user)
        mocks = self._mocks_por_tabela(
            mock_supabase,
            ('simulados', 'view_simulados_publicos', 'simulados_questoes',
             'alternativas_questao', 'simulados_resultados'),
        )

        mock_safe_execute.side_effect = [
            MagicMock(data=[]),                                  # tabela esconde o alheio
            MagicMock(data=[self._simulado_publico_alheio()]),    # view pública permite
            MagicMock(data=[{'id_questao': 20}]),                # simulado_questoes
            MagicMock(data=[{'id_questao': 20, 'letra': 'B'}]),  # gabarito
            MagicMock(data=[]),                                  # insert resultado
            MagicMock(data=[]),                                  # RPC ranking
        ]
        mock_supabase.rpc.return_value = MagicMock(data=[])

        response = self.client.post(
            f'/aluno/simulados/corrigir/{self.ID_SIMULADO}',
            data={'resp_20': 'B'},
        )

        self.assertEqual(response.status_code, 200)
        mocks['simulados_resultados'].insert.assert_called_once()

    @patch('rotas.simulado.supabase')
    @patch('rotas.simulado.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_ranking_simulado_privado_proprio_permite(
        self, mock_get_user, mock_safe_execute, mock_supabase
    ):
        self._autenticar_aluno(mock_get_user)
        mock_safe_execute.side_effect = [
            MagicMock(data=[self._simulado_proprio_privado()]),
            MagicMock(data=[]),  # RPC ranking
        ]
        mock_supabase.rpc.return_value = MagicMock(data=[])

        response = self.client.get(f'/aluno/simulados/ranking/{self.ID_SIMULADO}')

        self.assertEqual(response.status_code, 200)
        mock_supabase.rpc.assert_called_once_with(
            'ranking_simulado', {'p_id_simulado': self.ID_SIMULADO}
        )


if __name__ == '__main__':
    unittest.main()
