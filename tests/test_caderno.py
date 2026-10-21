import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configura o ambiente de testes
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'teste-chave-secreta-caderno')

from app import app

class TestCadernoBlueprint(unittest.TestCase):

    def setUp(self):
        """Inicializa o cliente de testes do Flask antes de cada teste."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['LOGIN_DISABLED'] = True  # Ignora o decorator @login_required do Flask-Login
        self.client = app.test_client()

    # -------------------------------------------------------------------------
    # Testes das Rotas de Visualização (Painel e Detalhes)
    # -------------------------------------------------------------------------

    @patch('rotas.caderno.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_meus_cadernos_sucesso(self, mock_get_user, mock_safe_execute):
        """Garante a renderização bem-sucedida da listagem de cadernos do aluno."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_user.tema = 'light'
        mock_get_user.return_value = mock_user

        mock_res = MagicMock()
        mock_res.data = [
            {"id_caderno": 1, "nome_caderno": "Meus Favoritos", "id_usuario": 12345, "criado_em": "2026-05-21T12:00:00"}
        ]
        mock_safe_execute.return_value = mock_res

        response = self.client.get('/aluno/meus_cadernos')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Meus Favoritos", response.data.decode('utf-8'))

    @patch('rotas.caderno.supabase')
    @patch('flask_login.utils._get_user')
    def test_visualizar_caderno_com_historico(self, mock_get_user, mock_supabase):
        """Valida que o caderno exiba as questões salvas correlacionando o histórico de acertos e erros."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        # Configura a sessão de testes com o id_usuario requerido pela rota
        with self.client.session_transaction() as sess:
            sess['id_usuario'] = 12345

        # Mocks das consultas em cascata do Supabase
        # 1. Nome do caderno
        mock_res_nome = MagicMock()
        mock_res_nome.data = {"nome_caderno": "Caderno de Constitucional"}
        
        # 2. IDs das questões vinculadas ao caderno
        mock_res_ids = MagicMock()
        mock_res_ids.data = [{"id_questao": 10}, {"id_questao": 11}]

        # 3. Detalhes das questões
        mock_res_detalhes = MagicMock()
        mock_res_detalhes.data = [
            {"id_questao": 10, "enunciado": "Questao 10", "alternativas_questao": []},
            {"id_questao": 11, "enunciado": "Questao 11", "alternativas_questao": []}
        ]

        # 4. Histórico de respostas do aluno para as questões (10: acerto, 11: erro)
        mock_res_historico = MagicMock()
        mock_res_historico.data = [
            {"id_questao": 10, "is_correct": True},
            {"id_questao": 11, "is_correct": False}
        ]

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_res_nome
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res_ids
        
        # Detalhes das questões e histórico de acertos/erros
        mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_res_detalhes
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.in_.return_value.execute.return_value = mock_res_historico

        response = self.client.get('/aluno/caderno/1')
        self.assertEqual(response.status_code, 200)
        conteudo = response.data.decode('utf-8')
        self.assertIn("Caderno de Constitucional", conteudo)
        self.assertIn("Questao 10", conteudo)
        self.assertIn("Questao 11", conteudo)

    # -------------------------------------------------------------------------
    # Testes das APIs de Listagem e Criação
    # -------------------------------------------------------------------------

    @patch('rotas.caderno.supabase')
    @patch('flask_login.utils._get_user')
    def test_listar_cadernos_api(self, mock_get_user, mock_supabase):
        """Garante que a API de listagem retorne o array JSON correspondente aos cadernos do usuário."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_res = MagicMock()
        mock_res.data = [{"id_caderno": 1, "nome_caderno": "Meus Favoritos"}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res

        response = self.client.get('/api/cadernos')
        self.assertEqual(response.status_code, 200)
        dados = response.get_json()
        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0]["nome_caderno"], "Meus Favoritos")

    @patch('rotas.caderno.supabase')
    @patch('flask_login.utils._get_user')
    def test_criar_caderno_sucesso(self, mock_get_user, mock_supabase):
        """Garante a inserção e criação bem-sucedida do caderno."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_res = MagicMock()
        mock_res.data = [{"id_caderno": 2, "nome_caderno": "Direito Civil", "id_usuario": 12345}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_res

        response = self.client.post('/api/cadernos/novo', json={"nome": "Direito Civil"})
        self.assertEqual(response.status_code, 200)
        dados = response.get_json()
        self.assertTrue(dados["success"])
        self.assertEqual(dados["caderno"]["nome_caderno"], "Direito Civil")

    @patch('flask_login.utils._get_user')
    def test_criar_caderno_sem_nome(self, mock_get_user):
        """Retorna erro 400 se tentar criar caderno com payload vazio."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_get_user.return_value = mock_user

        response = self.client.post('/api/cadernos/novo', json={})
        self.assertEqual(response.status_code, 400)
        dados = response.get_json()
        self.assertEqual(dados["error"], "Nome do caderno é obrigatório")

    # -------------------------------------------------------------------------
    # Testes de Operações Dinâmicas (Adição, Remoção e Exclusão)
    # -------------------------------------------------------------------------

    @patch('rotas.caderno.supabase')
    @patch('flask_login.utils._get_user')
    def test_salvar_questao_no_caderno_sucesso(self, mock_get_user, mock_supabase):
        """Grava com sucesso a relação questão-caderno no Supabase."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()

        response = self.client.post('/api/cadernos/salvar', json={
            "id_caderno": 1,
            "id_questao": 10
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    @patch('rotas.caderno.safe_execute')
    @patch('flask_login.utils._get_user')
    def test_salvar_questao_duplicada(self, mock_get_user, mock_safe_execute):
        """Retorna erro 400 amigável em caso de violação de restrição única (questão duplicada)."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        # Lança exceção de chave duplicada simulada pelo banco
        mock_safe_execute.side_effect = Exception("duplicate key value violates unique constraint")

        response = self.client.post('/api/cadernos/salvar', json={
            "id_caderno": 1,
            "id_questao": 10
        })
        self.assertEqual(response.status_code, 400)
        dados = response.get_json()
        self.assertFalse(dados["success"])
        self.assertEqual(dados["error"], "Esta questão já está neste caderno")

    @patch('rotas.caderno.supabase')
    @patch('flask_login.utils._get_user')
    def test_excluir_caderno_sucesso(self, mock_get_user, mock_supabase):
        """Exclui com sucesso o caderno do aluno ativo."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

        response = self.client.post('/api/cadernos/excluir/1')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    @patch('rotas.caderno.supabase')
    @patch('flask_login.utils._get_user')
    def test_remover_questao_caderno_sucesso(self, mock_get_user, mock_supabase):
        """Deleta com sucesso a vinculação de uma questão ao caderno do aluno."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

        response = self.client.post('/api/cadernos/remover_questao', json={
            "id_caderno": "1",
            "id_questao": "10"
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    @patch('flask_login.utils._get_user')
    def test_remover_questao_caderno_formato_invalido(self, mock_get_user):
        """Retorna erro 400 se o ID da questão fornecido for uma string não numérica."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        response = self.client.post('/api/cadernos/remover_questao', json={
            "id_caderno": "1",
            "id_questao": "texto_invalido"
        })
        self.assertEqual(response.status_code, 400)
        dados = response.get_json()
        self.assertFalse(dados["success"])
        self.assertEqual(dados["error"], "Formato do ID da questão inválido.")

if __name__ == '__main__':
    unittest.main()
