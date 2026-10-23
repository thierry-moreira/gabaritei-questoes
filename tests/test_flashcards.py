import os
import sys
import unittest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock, ANY

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configura o ambiente de testes
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'teste-chave-secreta-flashcards')

from app import app

class TestFlashcardsBlueprint(unittest.TestCase):

    def setUp(self):
        """Inicializa o cliente de testes do Flask antes de cada teste."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['LOGIN_DISABLED'] = True  # Ignora o decorator @login_required do Flask-Login
        self.client = app.test_client()

    # -------------------------------------------------------------------------
    # Testes de Acesso e Segurança
    # -------------------------------------------------------------------------

    @patch('flask_login.utils._get_user')
    def test_index_acesso_todos_usuarios(self, mock_get_user):
        """Todos os usuários autenticados têm acesso ao dashboard de flashcards (software livre)."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_get_user.return_value = mock_user

        response = self.client.get('/aluno/flashcards')
        self.assertEqual(response.status_code, 200)

    @patch('rotas.flashcards.supabase')
    @patch('flask_login.utils._get_user')
    def test_index_listagem_sucesso(self, mock_get_user, mock_supabase):
        """Usuário autenticado acessa o painel de flashcards com listagem de categorias e revisões do dia."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        # Mock das categorias
        mock_res_cat = MagicMock()
        mock_res_cat.data = [
            {"id_categoria": 1, "nome_categoria": "Direito Constitucional", "id_usuario": 12345}
        ]
        
        # Mock das revisões do dia
        mock_res_revisar = MagicMock()
        mock_res_revisar.count = 5

        # Configura individualmente cada cadeia para evitar fragilidades com side_effect
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res_cat
        mock_supabase.table.return_value.select.return_value.eq.return_value.lte.return_value.execute.return_value = mock_res_revisar

        response = self.client.get('/aluno/flashcards')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Direito Constitucional", response.data.decode('utf-8'))

    # -------------------------------------------------------------------------
    # Testes de Visualização e Estudo
    # -------------------------------------------------------------------------

    @patch('rotas.flashcards.supabase')
    @patch('flask_login.utils._get_user')
    def test_gerenciar_categoria_sucesso(self, mock_get_user, mock_supabase):
        """Carrega a página de gerenciamento de uma categoria com seus flashcards ordenados."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_res_cat = MagicMock()
        mock_res_cat.data = {"id_categoria": 1, "nome_categoria": "Direito Civil"}
        
        mock_res_cards = MagicMock()
        mock_res_cards.data = [
            {"id_flashcard": 10, "frente": "Pergunta 1", "verso": "Resposta 1", "id_categoria": 1}
        ]

        # Encadeamento para single() e order()
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_res_cat
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = mock_res_cards

        response = self.client.get('/aluno/flashcards/categoria/1')
        self.assertEqual(response.status_code, 200)
        conteudo = response.data.decode('utf-8')
        self.assertIn("Direito Civil", conteudo)
        self.assertIn("Pergunta 1", conteudo)

    @patch('rotas.flashcards.supabase')
    @patch('flask_login.utils._get_user')
    def test_gerenciar_categoria_inexistente(self, mock_get_user, mock_supabase):
        """Redireciona para o index se a categoria não existir ou não pertencer ao aluno."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_res_cat = MagicMock()
        mock_res_cat.data = None  # Categoria inexistente

        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_res_cat

        response = self.client.get('/aluno/flashcards/categoria/999')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/aluno/flashcards'))

    @patch('rotas.flashcards.supabase')
    @patch('flask_login.utils._get_user')
    def test_estudar_cards_carregamento(self, mock_get_user, mock_supabase):
        """Valida que a página de estudos carregue os cards programados para revisão."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_res_cards = MagicMock()
        mock_res_cards.data = [
            {"id_flashcard": 10, "frente": "Card 1", "verso": "Resposta 1", "id_categoria": 1}
        ]

        # Estudar categoria específica
        mock_supabase.table.return_value.select.return_value.eq.return_value.lte.return_value.eq.return_value.execute.return_value = mock_res_cards
        response = self.client.get('/aluno/flashcards/estudar/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Card 1", response.data.decode('utf-8'))

        # Estudar todas as categorias
        mock_supabase.table.return_value.select.return_value.eq.return_value.lte.return_value.execute.return_value = mock_res_cards
        response = self.client.get('/aluno/flashcards/estudar/todos')
        self.assertEqual(response.status_code, 200)

    # -------------------------------------------------------------------------
    # Testes das APIs (Criação e Exclusão)
    # -------------------------------------------------------------------------

    @patch('rotas.flashcards.supabase')
    @patch('flask_login.utils._get_user')
    def test_criar_categoria_api_sucesso(self, mock_get_user, mock_supabase):
        """Garante a criação de uma nova categoria com nome válido."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_res = MagicMock()
        mock_res.data = [{"id_categoria": 5, "nome_categoria": "Direito Penal", "id_usuario": "12345"}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_res

        response = self.client.post('/api/flashcards/categoria/nova', json={"nome": "Direito Penal"})
        self.assertEqual(response.status_code, 200)
        dados = response.get_json()
        self.assertTrue(dados["success"])
        self.assertEqual(dados["categoria"]["nome_categoria"], "Direito Penal")

    @patch('flask_login.utils._get_user')
    def test_criar_categoria_api_valida_nome(self, mock_get_user):
        """Retorna erro 400 se tentar criar categoria sem passar o nome."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_get_user.return_value = mock_user

        response = self.client.post('/api/flashcards/categoria/nova', json={})
        self.assertEqual(response.status_code, 400)
        dados = response.get_json()
        self.assertFalse(dados["success"])
        self.assertIn("Nome obrigatório", dados["error"])

    @patch('rotas.flashcards.supabase')
    @patch('flask_login.utils._get_user')
    def test_criar_card_api_sucesso(self, mock_get_user, mock_supabase):
        """Garante a criação de um flashcard com frente, verso e categoria válidos."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_res = MagicMock()
        mock_res.data = [{"id_flashcard": 100, "frente": "Q", "verso": "A"}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_res

        response = self.client.post('/api/flashcards/criar', json={
            "id_categoria": 1,
            "frente": "Pergunta Importante",
            "verso": "Resposta Importante"
        })
        self.assertEqual(response.status_code, 200)
        dados = response.get_json()
        self.assertTrue(dados["success"])
        self.assertEqual(dados["card"]["id_flashcard"], 100)

    @patch('flask_login.utils._get_user')
    def test_criar_card_api_campos_obrigatorios(self, mock_get_user):
        """Retorna erro 400 se tentar criar card sem fornecer frente ou verso."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_get_user.return_value = mock_user

        response = self.client.post('/api/flashcards/criar', json={"id_categoria": 1})
        self.assertEqual(response.status_code, 400)
        dados = response.get_json()
        self.assertFalse(dados["success"])

    # -------------------------------------------------------------------------
    # Testes do Algoritmo SM-2 (Repetição Espaçada)
    # -------------------------------------------------------------------------

    @patch('rotas.flashcards.supabase')
    @patch('flask_login.utils._get_user')
    def test_algoritmo_sm2_qualidade_zero(self, mock_get_user, mock_supabase):
        """Algoritmo Anki SM-2: Erro total (qualidade 0) zera o intervalo e reduz a facilidade em 0.2."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        # Estado inicial do card
        mock_res_select = MagicMock()
        mock_res_select.data = {
            "id_flashcard": 10,
            "id_usuario": 12345,
            "intervalo": 4,
            "facilidade": 2.5
        }
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_res_select

        response = self.client.post('/api/flashcards/revisar', json={
            "id_flashcard": 10,
            "qualidade": 0
        })
        self.assertEqual(response.status_code, 200)
        
        # O novo intervalo deve ser 0
        self.assertEqual(response.get_json()["novo_intervalo"], 0)
        
        # Valida se executou o update com facilidade reduzida: 2.5 - 0.2 = 2.3
        mock_supabase.table.return_value.update.assert_called_once_with({
            "intervalo": 0,
            "facilidade": 2.3,
            "proxima_revisao": ANY
        })

    @patch('rotas.flashcards.supabase')
    @patch('flask_login.utils._get_user')
    def test_algoritmo_sm2_qualidade_um(self, mock_get_user, mock_supabase):
        """Algoritmo Anki SM-2: Erro leve (qualidade 1) incrementa o intervalo levemente e reduz facilidade em 0.15."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_res_select = MagicMock()
        mock_res_select.data = {
            "id_flashcard": 10,
            "id_usuario": 12345,
            "intervalo": 10,
            "facilidade": 2.0
        }
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_res_select

        response = self.client.post('/api/flashcards/revisar', json={
            "id_flashcard": 10,
            "qualidade": 1
        })
        self.assertEqual(response.status_code, 200)
        
        # Novo intervalo = max(1, int(10 * 1.2)) = 12
        self.assertEqual(response.get_json()["novo_intervalo"], 12)
        
        # Facilidade = 2.0 - 0.15 = 1.85
        mock_supabase.table.return_value.update.assert_called_once_with({
            "intervalo": 12,
            "facilidade": 1.85,
            "proxima_revisao": ANY
        })

    @patch('rotas.flashcards.supabase')
    @patch('flask_login.utils._get_user')
    def test_algoritmo_sm2_qualidade_dois(self, mock_get_user, mock_supabase):
        """Algoritmo Anki SM-2: Acerto com esforço (qualidade 2) mantém facilidade e escala o intervalo por facilidade."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        # Cenário 2.a: intervalo == 0
        mock_res_select_a = MagicMock()
        mock_res_select_a.data = {"id_flashcard": 10, "id_usuario": 12345, "intervalo": 0, "facilidade": 2.5}
        
        # Cenário 2.b: intervalo == 1
        mock_res_select_b = MagicMock()
        mock_res_select_b.data = {"id_flashcard": 10, "id_usuario": 12345, "intervalo": 1, "facilidade": 2.5}

        # Cenário 2.c: intervalo > 1 (ex: 4)
        mock_res_select_c = MagicMock()
        mock_res_select_c.data = {"id_flashcard": 10, "id_usuario": 12345, "intervalo": 4, "facilidade": 2.5}

        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.side_effect = [
            mock_res_select_a, mock_res_select_b, mock_res_select_c
        ]

        # Execução 2.a (intervalo 0 -> 1)
        response = self.client.post('/api/flashcards/revisar', json={"id_flashcard": 10, "qualidade": 2})
        self.assertEqual(response.get_json()["novo_intervalo"], 1)

        # Execução 2.b (intervalo 1 -> 4)
        response = self.client.post('/api/flashcards/revisar', json={"id_flashcard": 10, "qualidade": 2})
        self.assertEqual(response.get_json()["novo_intervalo"], 4)

        # Execução 2.c (intervalo 4 -> int(4 * 2.5) = 10)
        response = self.client.post('/api/flashcards/revisar', json={"id_flashcard": 10, "qualidade": 2})
        self.assertEqual(response.get_json()["novo_intervalo"], 10)

    @patch('rotas.flashcards.supabase')
    @patch('flask_login.utils._get_user')
    def test_algoritmo_sm2_qualidade_tres(self, mock_get_user, mock_supabase):
        """Algoritmo Anki SM-2: Acerto fácil (qualidade 3) aumenta a facilidade em 0.15 e escala o intervalo agressivamente."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_res_select = MagicMock()
        mock_res_select.data = {
            "id_flashcard": 10,
            "id_usuario": 12345,
            "intervalo": 4,
            "facilidade": 2.2
        }
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_res_select

        response = self.client.post('/api/flashcards/revisar', json={
            "id_flashcard": 10,
            "qualidade": 3
        })
        self.assertEqual(response.status_code, 200)
        
        # Novo intervalo = int(4 * 2.2 * 1.3) = 11
        self.assertEqual(response.get_json()["novo_intervalo"], 11)
        
        # Nova facilidade = min(2.5, 2.2 + 0.15) = 2.35
        mock_supabase.table.return_value.update.assert_called_once_with({
            "intervalo": 11,
            "facilidade": 2.35,
            "proxima_revisao": ANY
        })

    # -------------------------------------------------------------------------
    # Testes de Remoção
    # -------------------------------------------------------------------------

    @patch('rotas.flashcards.supabase')
    @patch('flask_login.utils._get_user')
    def test_excluir_card_api(self, mock_get_user, mock_supabase):
        """Garante a exclusão permanente de um card pelo ID."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

        response = self.client.post('/api/flashcards/excluir/100')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    @patch('rotas.flashcards.supabase')
    @patch('flask_login.utils._get_user')
    def test_excluir_categoria_api(self, mock_get_user, mock_supabase):
        """Garante a exclusão permanente de uma categoria completa e seus cards."""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.role = 'aluno'
        mock_user.id = 12345
        mock_get_user.return_value = mock_user

        mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

        response = self.client.post('/api/flashcards/categoria/excluir/5')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

if __name__ == '__main__':
    unittest.main()
