import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configura o ambiente de testes
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'teste-chave-secreta-ia-provisoria')

from app import app

class TestIAChatBlueprint(unittest.TestCase):
    
    def setUp(self):
        """Inicializa o cliente de testes do Flask antes de cada teste."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    # -------------------------------------------------------------------------
    # Testes da Rota de Explicação Pedagógica (/api/ia_explica)
    # -------------------------------------------------------------------------

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.safe_execute')
    @patch('rotas.questao.supabase')
    def test_ia_explica_com_cache(self, mock_supabase, mock_safe_execute, mock_questao_user, mock_utils_user):
        """Valida que o endpoint retorna explicação existente do cache global (explicacoes_ia) de imediato."""
        for mock_user in [mock_questao_user, mock_utils_user]:
            mock_user.is_authenticated = True
            mock_user.id = '12345'
            mock_user.plano = 'premium'
            mock_user.role = 'aluno'

        # Mock da query de cache que encontra explicação
        mock_res_cache = MagicMock()
        mock_res_cache.data = [{'conteudo_explicacao': "Explicação já cacheada e perfeita no banco de dados."}]
        mock_safe_execute.return_value = mock_res_cache

        response = self.client.post('/api/ia_explica', json={'id_questao': 500})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Explicação já cacheada", response.get_json().get('explicacao', ''))

    @patch('utils.current_user')
    @patch('rotas.questao.client_gpt')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.safe_execute')
    @patch('rotas.questao.supabase')
    def test_ia_explica_geracao_sucesso(self, mock_supabase, mock_safe_execute, mock_questao_user, mock_client_gpt, mock_utils_user):
        """Garante a geração inédita da explicação via OpenAI quando não há cache, tratando a limpeza e a gravação."""
        for mock_user in [mock_questao_user, mock_utils_user]:
            mock_user.is_authenticated = True
            mock_user.id = '12345'
            mock_user.plano = 'premium'
            mock_user.role = 'aluno'

        # Configura respostas sucessivas de safe_execute:
        # 1. Busca cache explicacoes_ia (Vazio)
        mock_res_cache = MagicMock()
        mock_res_cache.data = []

        # 2. Busca dados da questão (Tabela questoes)
        mock_res_q = MagicMock()
        mock_res_q.data = {
            'id_questao': 500,
            'enunciado': 'A constituição é rígida?',
            'url_imagem': None
        }

        # 3. Busca alternativas
        mock_res_alt = MagicMock()
        mock_res_alt.data = [
            {'letra': 'A', 'is_correct': True, 'texto': 'Sim, alterável apenas por PEC.'},
            {'letra': 'B', 'is_correct': False, 'texto': 'Não, é flexível.'}
        ]

        # 4. Salva no cache final (safe_execute de insert)
        mock_res_insert = MagicMock()

        mock_safe_execute.side_effect = [
            mock_res_cache,
            mock_res_q,
            mock_res_alt,
            mock_res_insert
        ]

        # Configura o retorno mock da OpenAI
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "> A constituição brasileira de 1988 é classificada como rígida."
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client_gpt.chat.completions.create.return_value = mock_response

        response = self.client.post('/api/ia_explica', json={'id_questao': 500})
        self.assertEqual(response.status_code, 200)
        
        dados = response.get_json()
        self.assertIn("constituição brasileira", dados.get('explicacao', ''))
        
        # Garante que limpou o caractere '>' conforme regra sanitizar_latex/back-end safety
        self.assertNotIn("> ", dados.get('explicacao', ''))
        mock_client_gpt.chat.completions.create.assert_called_once()

    # -------------------------------------------------------------------------
    # Testes do Gerador de Materiais (/api/ia/gerar_estudo)
    # -------------------------------------------------------------------------

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.safe_execute')
    @patch('rotas.questao.supabase')
    def test_ia_gerar_estudo_resumo_cache_usuario(self, mock_supabase, mock_safe_execute, mock_questao_user, mock_utils_user):
        """Valida que se o resumo de estudo já existir no caderno do próprio aluno, retorna a notificação de cache hit."""
        for mock_user in [mock_questao_user, mock_utils_user]:
            mock_user.is_authenticated = True
            mock_user.id = '12345'
            mock_user.plano = 'premium'
            mock_user.role = 'aluno'

        # Mock da busca da questão
        mock_res_q = MagicMock()
        mock_res_q.data = {'id_questao': 500, 'id_materia': 1, 'nome_materia': 'Direito'}

        # Mock da verificação se já existe resumo salvo
        mock_res_check = MagicMock()
        mock_res_check.data = {'id_resumo': 99}

        mock_safe_execute.side_effect = [mock_res_q, mock_res_check]

        response = self.client.post('/api/ia/gerar_estudo', json={
            'id_questao': 500,
            'tipo': 'resumo'
        })
        self.assertEqual(response.status_code, 200)
        dados = response.get_json()
        self.assertTrue(dados.get('success'))
        self.assertTrue(dados.get('cache'))
        self.assertIn("já está no seu caderno", dados.get('mensagem', ''))

    @patch('utils.current_user')
    @patch('rotas.questao.client_gpt')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.safe_execute')
    @patch('rotas.questao.supabase')
    def test_ia_gerar_estudo_flashcard_geracao_nova(self, mock_supabase, mock_safe_execute, mock_questao_user, mock_client_gpt, mock_utils_user):
        """Valida a geração inédita de flashcard pela OpenAI quando não há cache local ou global, salvando no banco."""
        for mock_user in [mock_questao_user, mock_utils_user]:
            mock_user.is_authenticated = True
            mock_user.id = '12345'
            mock_user.plano = 'premium'
            mock_user.role = 'aluno'

        # Mock sequencial do safe_execute:
        # 1. Busca dados da questão
        mock_res_q = MagicMock()
        mock_res_q.data = {'id_questao': 500, 'id_materia': 1, 'nome_materia': 'Direito', 'enunciado': 'A constituição garante...'}

        # 2. Busca cache de flashcard do usuário (Vazio)
        mock_res_check = MagicMock()
        mock_res_check.data = None

        # 3. Busca cache global ia_cache_estudo (Vazio)
        mock_res_global = MagicMock()
        mock_res_global.data = None

        # 4. Busca explicações anteriores para contexto
        mock_res_exp = MagicMock()
        mock_res_exp.data = [{'conteudo_explicacao': 'Explicação prévia.'}]

        # 5. Busca alternativas da questão
        mock_res_alt = MagicMock()
        mock_res_alt.data = [{'letra': 'C', 'is_correct': True}]

        # 6. Busca template da matéria
        mock_res_prompt = MagicMock()
        mock_res_prompt.data = []

        # 7. Salva o flashcard gerado no cache global
        mock_res_save_global = MagicMock()

        # 8. Busca categoria do flashcard (Simula categoria 'Direito' já existente)
        mock_res_cat = MagicMock()
        mock_res_cat.data = [{'id_categoria': 99}]

        # 9. Salva o flashcard gerado no banco do usuário
        mock_res_save_user = MagicMock()

        mock_safe_execute.side_effect = [
            mock_res_q,
            mock_res_check,
            mock_res_global,
            mock_res_exp,
            mock_res_alt,
            mock_res_prompt,
            mock_res_save_global,
            mock_res_cat,
            mock_res_save_user
        ]

        # Mock OpenAI completions
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"pergunta": "Qual a característica X?", "resposta": "Característica Y."}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client_gpt.chat.completions.create.return_value = mock_response

        response = self.client.post('/api/ia/gerar_estudo', json={
            'id_questao': 500,
            'tipo': 'flashcard'
        })
        self.assertEqual(response.status_code, 200)
        dados = response.get_json()
        self.assertTrue(dados.get('success'))
        self.assertNotIn("cache", dados)
        
        # Garante chamada OpenAI
        mock_client_gpt.chat.completions.create.assert_called_once()

if __name__ == '__main__':
    unittest.main()
