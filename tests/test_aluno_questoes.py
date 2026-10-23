import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configura o ambiente de testes
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'teste-chave-secreta-provisoria')

# Importa a aplicação Flask oficial
from app import app

class TestAlunoQuestaoFlask(unittest.TestCase):
    
    def setUp(self):
        """Inicializa o cliente de testes do Flask antes de cada teste."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    # -------------------------------------------------------------------------
    # Testes de Painel e Dashboards (GET)
    # -------------------------------------------------------------------------
    
    @patch('utils.current_user')
    @patch('rotas.aluno.current_user')
    @patch('rotas.aluno.safe_execute')
    @patch('rotas.aluno.supabase')
    def test_painel_aluno_sucesso(self, mock_supabase, mock_safe_execute, mock_aluno_current_user, mock_utils_current_user):
        """Valida que o painel do aluno calcula acertos, erros e streak de forma mockada com sucesso."""
        for mock_user in [mock_aluno_current_user, mock_utils_current_user]:
            mock_user.is_authenticated = True
            mock_user.role = 'aluno'
            mock_user.id = '99988'
        
        # Configura as respostas consecutivas do safe_execute:
        # 1. Total resolvidas (Count)
        mock_res_total = MagicMock()
        mock_res_total.count = 10
        
        # 2. Total acertos (Count)
        mock_res_acertos = MagicMock()
        mock_res_acertos.count = 7
        
        # 3. Histórico de respostas (Data) - Simula streak de 2 dias
        mock_res_historico = MagicMock()
        hoje_br = (datetime.now() - timedelta(hours=3))
        ontem_br = hoje_br - timedelta(days=1)
        
        mock_res_historico.data = [
            {'criado_em': hoje_br.strftime('%Y-%m-%dT12:00:00Z'), 'is_correct': True},
            {'criado_em': ontem_br.strftime('%Y-%m-%dT10:00:00Z'), 'is_correct': False}
        ]
        
        # Retorna na ordem das queries realizadas no endpoint:
        mock_safe_execute.side_effect = [mock_res_total, mock_res_acertos, mock_res_historico]
        
        response = self.client.get('/aluno/painel')
        self.assertEqual(response.status_code, 200)
        # Deve renderizar o painel e calcular a taxa de acertos (7 de 10 = 70%) e streak (2 dias)
        self.assertIn(b'70%', response.data)
        self.assertIn(b'2', response.data)
        self.assertIn(b'dias de estudo constante', response.data.lower())
        
        # Garante que o pedagógio invisible de expiração premium rodou

    @patch('utils.current_user')
    @patch('rotas.aluno.current_user')
    @patch('rotas.aluno.safe_execute')
    @patch('rotas.aluno.supabase')
    def test_dashboard_detalhado_sucesso(self, mock_supabase, mock_safe_execute, mock_aluno_current_user, mock_utils_current_user):
        """Valida o processamento do dashboard detalhado por matéria, tópicos e curvas de esquecimento."""
        for mock_user in [mock_aluno_current_user, mock_utils_current_user]:
            mock_user.is_authenticated = True
            mock_user.role = 'aluno'
            mock_user.id = '99988'
            mock_user.meta_diaria = 10

        # Mocks consecutivos para o dashboard detalhado:
        # 1. Histórico de respostas (5 resolvidas de Direito Constitucional, id_questao=1)
        mock_res_hist = MagicMock()
        criado_antigo = datetime.utcnow() - timedelta(days=5) # 5 dias atrás (REVISAR)
        mock_res_hist.data = [
            {'id_questao': 1, 'is_correct': True, 'criado_em': criado_antigo.strftime('%Y-%m-%dT12:00:00Z')},
            {'id_questao': 1, 'is_correct': True, 'criado_em': criado_antigo.strftime('%Y-%m-%dT13:00:00Z')},
            {'id_questao': 1, 'is_correct': True, 'criado_em': criado_antigo.strftime('%Y-%m-%dT14:00:00Z')},
            {'id_questao': 1, 'is_correct': True, 'criado_em': criado_antigo.strftime('%Y-%m-%dT15:00:00Z')},
            {'id_questao': 1, 'is_correct': False, 'criado_em': criado_antigo.strftime('%Y-%m-%dT16:00:00Z')}
        ]

        # 2. View completa das questões (Metadados da questão 1)
        mock_res_meta = MagicMock()
        mock_res_meta.data = [{
            'id_questao': 1,
            'id_materia': 10,
            'nome_materia': 'Direito Constitucional',
            'id_topico': 100,
            'nome_topico': 'Direitos Fundamentais'
        }]

        mock_safe_execute.side_effect = [mock_res_hist, mock_res_meta]

        response = self.client.get('/aluno/dashboard_detalhado')
        self.assertEqual(response.status_code, 200)
        
        # Deve identificar taxa de acerto (4 de 5 = 80%), classificar como Melhor Matéria (mínimo 5 resolvidas)
        # E disparar alerta de "REVISAR" para o atraso de 5 dias
        self.assertIn(b'Direito Constitucional', response.data)
        self.assertIn(b'revisar', response.data.lower())
        self.assertIn(b'80%', response.data)

    @patch('utils.current_user')
    @patch('rotas.aluno.current_user')
    @patch('rotas.aluno.safe_execute')
    @patch('rotas.aluno.supabase')
    def test_dashboard_detalhado_vazio(self, mock_supabase, mock_safe_execute, mock_aluno_current_user, mock_utils_current_user):
        """Garante que alunos sem histórico sejam redirecionados para o painel principal com flash informando."""
        for mock_user in [mock_aluno_current_user, mock_utils_current_user]:
            mock_user.is_authenticated = True
            mock_user.role = 'aluno'
            mock_user.id = '99988'

        # Histórico de respostas vazio
        mock_res_hist = MagicMock()
        mock_res_hist.data = []
        mock_safe_execute.return_value = mock_res_hist

        response = self.client.get('/aluno/dashboard_detalhado')
        # Deve redirecionar para a área do aluno
        self.assertEqual(response.status_code, 302)
        self.assertIn('/aluno/painel', response.headers['Location'])

        # Verifica o flash message
        with self.client.session_transaction() as sess:
            flashes = sess.get('_flashes', [])
            self.assertTrue(any("Resolva algumas questões primeiro" in msg[1] for msg in flashes))


    # -------------------------------------------------------------------------
    # Testes de Resolução (POST)
    # -------------------------------------------------------------------------

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.safe_execute')
    @patch('rotas.questao.supabase')
    def test_responder_questao_aluno_sucesso(self, mock_supabase, mock_safe_execute, mock_questao_current_user, mock_utils_current_user):
        """Valida que a rota POST de resposta processa a alternativa correta e insere histórico."""
        for mock_user in [mock_questao_current_user, mock_utils_current_user]:
            mock_user.is_authenticated = True
            mock_user.role = 'aluno'
            mock_user.id = '99988'
        
        # Mocks consecutivos do safe_execute:
        # 1. Alternativas da questão (ID 50)
        mock_res_alt = MagicMock()
        mock_res_alt.data = [
            {'id_alternativa': 101, 'letra': 'A', 'is_correct': True},
            {'id_alternativa': 102, 'letra': 'B', 'is_correct': False}
        ]
        
        # 2. Comentário do gabarito da questão
        mock_res_coment = MagicMock()
        mock_res_coment.data = {'comentario_gabarito': 'Excelente comentário explicativo.'}

        # 3. Inserção do histórico
        mock_res_insert = MagicMock()

        mock_safe_execute.side_effect = [
            mock_res_alt,
            mock_res_coment,
            mock_res_insert
        ]

        # Submete alternativa A (que é a correta)
        response = self.client.post('/aluno/responder', json={
            'questao_id': 50,
            'alternativa': 'A'
        })

        self.assertEqual(response.status_code, 200)
        
        dados = response.get_json()
        self.assertTrue(dados.get('sucesso'))
        self.assertTrue(dados.get('correta'))
        self.assertEqual(dados.get('letra_correta'), 'A')
        self.assertEqual(dados.get('comentario'), 'Excelente comentário explicativo.')

    # -------------------------------------------------------------------------
    # Testes de Moderação de Comentários (POST)
    # -------------------------------------------------------------------------

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('utils.verificar_texto_improprio')
    @patch('rotas.questao.safe_execute')
    @patch('rotas.questao.supabase')
    def test_salvar_comentario_sucesso(self, mock_supabase, mock_safe_execute, mock_moderacao, mock_questao_current_user, mock_utils_current_user):
        """Garante que comentários com linguajar aceitável sejam postados com sucesso."""
        for mock_user in [mock_questao_current_user, mock_utils_current_user]:
            mock_user.is_authenticated = True
            mock_user.role = 'aluno'
            mock_user.id = '99988'

        # Moderação aprova o texto
        mock_moderacao.return_value = (True, None)

        # 1. Busca username
        mock_res_user = MagicMock()
        mock_res_user.data = {'username': 'concurseiro_estudioso'}
        # 2. Inserção do comentário
        mock_res_insert = MagicMock()

        mock_safe_execute.side_effect = [mock_res_user, mock_res_insert]

        response = self.client.post('/api/comentarios', json={
            'id_questao': 50,
            'texto': 'Comentário muito produtivo e bem explicado!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json().get('success'))

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('utils.verificar_texto_improprio')
    def test_salvar_comentario_bloqueado_moderacao(self, mock_moderacao, mock_questao_current_user, mock_utils_current_user):
        """Garante que comentários contendo termos banidos sejam bloqueados com status 400."""
        for mock_user in [mock_questao_current_user, mock_utils_current_user]:
            mock_user.is_authenticated = True
            mock_user.role = 'aluno'
            mock_user.id = '99988'

        # Moderação reprova o texto
        mock_moderacao.return_value = (False, 'Linguajar inadequado detectado.')

        response = self.client.post('/api/comentarios', json={
            'id_questao': 50,
            'texto': 'PalavraFeia!'
        })
        # Deve barrar com status 400 (Bad Request)
        self.assertEqual(response.status_code, 400)
        
        dados = response.get_json()
        self.assertFalse(dados.get('success'))
        self.assertEqual(dados.get('error'), 'Linguajar inadequado detectado.')

    # -------------------------------------------------------------------------
    # Testes de Denúncia de Comentários (POST /api/comentarios/<id>/reportar)
    # Moderação humana: a denúncia vai para o painel do admin — sem IA.
    # -------------------------------------------------------------------------

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    def test_reportar_comentario_motivo_vazio(self, mock_questao_current_user, mock_utils_current_user):
        """Sem motivo selecionado, a denúncia é rejeitada com 400."""
        for mock_user in [mock_questao_current_user, mock_utils_current_user]:
            mock_user.is_authenticated = True
            mock_user.role = 'aluno'
            mock_user.id = '99988'

        response = self.client.post(
            '/api/comentarios/11111111-1111-1111-1111-111111111111/reportar',
            json={'motivo': '   '}
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json().get('success'))

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    def test_reportar_comentario_uuid_invalido(self, mock_questao_current_user, mock_utils_current_user):
        """IDs fora do formato uuid são rejeitados com 400."""
        for mock_user in [mock_questao_current_user, mock_utils_current_user]:
            mock_user.is_authenticated = True
            mock_user.role = 'aluno'
            mock_user.id = '99988'

        response = self.client.post(
            '/api/comentarios/nao-e-um-uuid/reportar',
            json={'motivo': 'Spam ou propaganda'}
        )
        self.assertEqual(response.status_code, 400)

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.safe_execute')
    @patch('rotas.questao.supabase')
    def test_reportar_comentario_sucesso(self, mock_supabase, mock_safe_execute, mock_questao_current_user, mock_utils_current_user):
        """Denúncia válida grava em reports_comentarios e confirma ao aluno."""
        for mock_user in [mock_questao_current_user, mock_utils_current_user]:
            mock_user.is_authenticated = True
            mock_user.role = 'aluno'
            mock_user.id = '99988'

        mock_res_comentario = MagicMock()
        mock_res_comentario.data = {'id_comentario': '11111111-1111-1111-1111-111111111111'}
        mock_res_insert = MagicMock()
        mock_safe_execute.side_effect = [mock_res_comentario, mock_res_insert]

        response = self.client.post(
            '/api/comentarios/11111111-1111-1111-1111-111111111111/reportar',
            json={'motivo': 'Conteúdo ofensivo ou desrespeitoso'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json().get('success'))

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.safe_execute')
    @patch('rotas.questao.supabase')
    def test_reportar_comentario_nao_encontrado(self, mock_supabase, mock_safe_execute, mock_questao_current_user, mock_utils_current_user):
        """Comentário inexistente responde 404 sem gravar nada."""
        for mock_user in [mock_questao_current_user, mock_utils_current_user]:
            mock_user.is_authenticated = True
            mock_user.role = 'aluno'
            mock_user.id = '99988'

        mock_res_comentario = MagicMock()
        mock_res_comentario.data = None
        mock_safe_execute.side_effect = [mock_res_comentario]

        response = self.client.post(
            '/api/comentarios/22222222-2222-2222-2222-222222222222/reportar',
            json={'motivo': 'Spam ou propaganda'}
        )
        self.assertEqual(response.status_code, 404)

    @patch('utils.current_user')
    @patch('rotas.questao.current_user')
    @patch('rotas.questao.safe_execute')
    @patch('rotas.questao.supabase')
    def test_reportar_comentario_duplicado_409(self, mock_supabase, mock_safe_execute, mock_questao_current_user, mock_utils_current_user):
        """Segunda denúncia do mesmo aluno no mesmo comentário → 409 amigável."""
        for mock_user in [mock_questao_current_user, mock_utils_current_user]:
            mock_user.is_authenticated = True
            mock_user.role = 'aluno'
            mock_user.id = '99988'

        mock_res_comentario = MagicMock()
        mock_res_comentario.data = {'id_comentario': '11111111-1111-1111-1111-111111111111'}
        mock_safe_execute.side_effect = [
            mock_res_comentario,
            Exception('duplicate key value violates unique constraint "reports_comentarios_pkey" (23505)'),
        ]

        response = self.client.post(
            '/api/comentarios/11111111-1111-1111-1111-111111111111/reportar',
            json={'motivo': 'Spam ou propaganda'}
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn('já denunciou', response.get_json().get('error', ''))

if __name__ == '__main__':
    unittest.main()
