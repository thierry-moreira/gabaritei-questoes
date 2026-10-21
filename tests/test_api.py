import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configura o ambiente de testes
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'teste-chave-secreta-api-auxiliar')

from app import app

class TestAPIBlueprint(unittest.TestCase):

    def setUp(self):
        """Inicializa o cliente de testes do Flask antes de cada teste."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    # -------------------------------------------------------------------------
    # Testes de Cargos por Órgão (/api/cargos/<id>)
    # -------------------------------------------------------------------------

    @patch('rotas.api.supabase')
    def test_api_cargos_por_orgao_sucesso(self, mock_supabase):
        """Garante que retorne os cargos ordenados correspondentes àquele órgão."""
        mock_response = MagicMock()
        mock_response.data = [
            {"id_cargo": 1, "nome_cargo": "Analista Judiciário"},
            {"id_cargo": 2, "nome_cargo": "Técnico Judiciário"}
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response

        response = self.client.get('/api/cargos/10')
        self.assertEqual(response.status_code, 200)
        
        dados = response.get_json()
        self.assertEqual(len(dados), 2)
        self.assertEqual(dados[0]["nome_cargo"], "Analista Judiciário")

    # -------------------------------------------------------------------------
    # Testes de Tópicos e Subtópicos em Cascata (/api/get_assuntos_cascata)
    # -------------------------------------------------------------------------

    @patch('flask_login.utils._get_user')
    def test_api_get_assuntos_cascata_vazia(self, mock_get_user):
        """Retorna uma lista vazia se nenhuma matéria for informada."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_get_user.return_value = mock_user

        response = self.client.post('/api/get_assuntos_cascata', json={"ids_materias": []})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    @patch('rotas.api.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_api_get_assuntos_cascata_sucesso(self, mock_get_user, mock_safe_execute):
        """Valida que monte a estrutura em árvore correlacionando tópicos a seus subtópicos."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_get_user.return_value = mock_user

        # 1. Mock dos tópicos retornados
        mock_res_topicos = MagicMock()
        mock_res_topicos.data = [
            {"id_topico": 100, "nome_topico": "Direito Constitucional"},
            {"id_topico": 101, "nome_topico": "Direito Administrativo"}
        ]

        # 2. Mock dos subtópicos retornados
        mock_res_sub = MagicMock()
        mock_res_sub.data = [
            {"id_subtopico": 200, "nome_subtopico": "Princípios", "id_topico": 100},
            {"id_subtopico": 201, "nome_subtopico": "Atos", "id_topico": 101}
        ]

        mock_safe_execute.side_effect = [mock_res_topicos, mock_res_sub]

        response = self.client.post('/api/get_assuntos_cascata', json={"ids_materias": [1, 2]})
        self.assertEqual(response.status_code, 200)

        dados = response.get_json()
        self.assertEqual(len(dados), 2)
        
        # Valida que o Direito Constitucional contém os Princípios
        self.assertEqual(dados[0]["nome"], "Direito Constitucional")
        self.assertEqual(len(dados[0]["subtopicos"]), 1)
        self.assertEqual(dados[0]["subtopicos"][0]["nome"], "Princípios")

    # -------------------------------------------------------------------------
    # Testes de Endpoints de Listagem Auxiliares
    # -------------------------------------------------------------------------

    @patch('rotas.api.safe_execute')
    def test_api_topicos_por_materia(self, mock_safe_execute):
        """Valida a listagem de tópicos filtrados por matéria."""
        mock_res = MagicMock()
        mock_res.data = [{"id_topico": 1, "nome_topico": "Princípio da Legalidade"}]
        mock_safe_execute.return_value = mock_res

        response = self.client.get('/api/topicos/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["nome_topico"], "Princípio da Legalidade")

    @patch('rotas.api.safe_execute')
    def test_api_subtopicos_por_topico(self, mock_safe_execute):
        """Valida a listagem de subtópicos filtrados por tópico."""
        mock_res = MagicMock()
        mock_res.data = [{"id_subtopico": 5, "nome_subtopico": "Legalidade Estrita"}]
        mock_safe_execute.return_value = mock_res

        response = self.client.get('/api/subtopicos/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["nome_subtopico"], "Legalidade Estrita")

    # -------------------------------------------------------------------------
    # Testes de Salvamento de Preferências (/api/usuario/preferencias)
    # -------------------------------------------------------------------------

    @patch('flask_login.utils._get_user')
    def test_salvar_preferencias_tema_invalido(self, mock_get_user):
        """Retorna 400 se o usuário tentar salvar um tema não cadastrado."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_get_user.return_value = mock_user

        response = self.client.post('/api/usuario/preferencias', json={"tema": "blue"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Tema inválido", response.get_json().get('error', ''))

    @patch('rotas.api.supabase')
    @patch('flask_login.utils._get_user')
    def test_salvar_preferencias_tema_sucesso(self, mock_get_user, mock_supabase):
        """Grava no banco a preferência do aluno (dark/light) com sucesso."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_res = MagicMock()
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_res

        response = self.client.post('/api/usuario/preferencias', json={"tema": "dark"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json().get('success'))
        
        mock_supabase.table.return_value.update.assert_called_once_with({"tema": "dark"})

if __name__ == '__main__':
    unittest.main()
