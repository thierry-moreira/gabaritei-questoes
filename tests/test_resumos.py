import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configura o ambiente de testes
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'teste-chave-secreta-resumos')

from app import app

class TestResumosBlueprint(unittest.TestCase):

    def setUp(self):
        """Inicializa o cliente de testes do Flask antes de cada teste."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['LOGIN_DISABLED'] = True  # Ignora o decorator @login_required do Flask-Login
        self.client = app.test_client()

    # -------------------------------------------------------------------------
    # Testes das Rotas de Visualização (Dashboard e Matéria Específica)
    # -------------------------------------------------------------------------

    @patch('flask_login.utils._get_user')
    def test_resumos_index_todos_usuarios(self, mock_get_user):
        """Todos os usuários autenticados têm acesso ao dashboard de resumos (software livre)."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.plano = 'premium'
        mock_get_user.return_value = mock_user

        response = self.client.get('/aluno/resumos')
        self.assertEqual(response.status_code, 200)

    @patch('rotas.resumos.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_resumos_index_premium_sucesso(self, mock_get_user, mock_safe_execute):
        """Garante a exibição do dashboard agrupado por matérias para usuários premium."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.plano = 'premium'
        mock_user.id = 12345
        mock_user.tema = 'light'
        mock_get_user.return_value = mock_user

        mock_res = MagicMock()
        mock_res.data = [
            {"id_materia": 2, "materias": {"nome_materia": "Direito Civil"}},
            {"id_materia": 2, "materias": {"nome_materia": "Direito Civil"}}
        ]
        mock_safe_execute.return_value = mock_res

        response = self.client.get('/aluno/resumos')
        self.assertEqual(response.status_code, 200)
        conteudo = response.data.decode('utf-8')
        self.assertIn("Direito Civil", conteudo)

    @patch('rotas.resumos.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_ver_resumos_materia_sucesso(self, mock_get_user, mock_safe_execute):
        """Renderiza a lista de resumos teóricos para uma matéria específica selecionada."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.plano = 'premium'
        mock_user.id = 12345
        mock_user.tema = 'light'
        mock_get_user.return_value = mock_user

        # Mock do nome da matéria
        mock_res_materia = MagicMock()
        mock_res_materia.data = {"nome_materia": "Direito Penal"}

        # Mock da listagem de resumos
        mock_res_lista = MagicMock()
        mock_res_lista.data = [
            {"id_resumo": 1, "titulo_resumo": "Exclusão de Ilicitude", "conteudo": "Exclusão de Ilicitude", "criado_em": "2026-05-21T18:00:00Z"}
        ]

        mock_safe_execute.side_effect = [mock_res_materia, mock_res_lista]

        response = self.client.get('/aluno/resumos/materia/3')
        self.assertEqual(response.status_code, 200)
        conteudo = response.data.decode('utf-8')
        self.assertIn("Direito Penal", conteudo)
        self.assertIn("Exclusão de Ilicitude", conteudo)

    @patch('rotas.resumos.supabase')
    @patch('flask_login.utils._get_user')
    def test_ver_resumos_materia_inexistente(self, mock_get_user, mock_supabase):
        """Retorna status 404 se tentar visualizar resumos de uma matéria não cadastrada."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.plano = 'premium'
        mock_get_user.return_value = mock_user

        mock_res_materia = MagicMock()
        mock_res_materia.data = None  # Matéria não encontrada

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_res_materia

        response = self.client.get('/aluno/resumos/materia/999')
        self.assertEqual(response.status_code, 404)

    # -------------------------------------------------------------------------
    # Testes das APIs (Exclusão)
    # -------------------------------------------------------------------------

    @patch('rotas.resumos.supabase')
    @patch('flask_login.utils._get_user')
    def test_excluir_resumo_sucesso(self, mock_get_user, mock_supabase):
        """Exclui com sucesso um resumo pelo ID do aluno ativo."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.plano = 'premium'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

        response = self.client.post('/api/resumos/excluir/10')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    @patch('rotas.resumos.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_excluir_resumo_erro(self, mock_get_user, mock_safe_execute):
        """Retorna success=False em caso de falha de conexão na exclusão do resumo."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.plano = 'premium'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        # Simula falha ao interagir com o banco
        mock_safe_execute.return_value = None

        response = self.client.post('/api/resumos/excluir/10')
        self.assertEqual(response.status_code, 200)
        dados = response.get_json()
        self.assertFalse(dados["success"])
        self.assertEqual(dados["error"], "Erro ao excluir resumo")

    @patch('rotas.resumos.supabase')
    @patch('flask_login.utils._get_user')
    def test_excluir_caderno_sucesso(self, mock_get_user, mock_supabase):
        """Exclui com sucesso todos os resumos de uma matéria (caderno inteiro) do aluno ativo."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.plano = 'premium'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

        response = self.client.post('/api/resumos/excluir-materia/3')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    @patch('rotas.resumos.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_excluir_caderno_erro(self, mock_get_user, mock_safe_execute):
        """Retorna success=False em caso de falha de conexão na exclusão do caderno inteiro."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.plano = 'premium'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        # Simula falha ao interagir com o banco
        mock_safe_execute.return_value = None

        response = self.client.post('/api/resumos/excluir-materia/3')
        self.assertEqual(response.status_code, 200)
        dados = response.get_json()
        self.assertFalse(dados["success"])
        self.assertEqual(dados["error"], "Erro ao excluir caderno")

if __name__ == '__main__':
    unittest.main()
