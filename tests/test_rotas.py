import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configura o ambiente de testes
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'teste-chave-secreta-provisoria')

# Importa a aplicação Flask oficial
from app import app

class TestRotasFlask(unittest.TestCase):
    
    def setUp(self):
        """Inicializa o cliente de testes do Flask antes de cada teste."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    # -------------------------------------------------------------------------
    # Testes de Honeypots de Segurança
    # -------------------------------------------------------------------------
    def test_admin_honeypots(self):
        """Garante que as rotas administrativas padrão barrem requisições com 404 (Honeypot)."""
        endpoints = ['/admin', '/admin/', '/admin/login']
        for rota in endpoints:
            with self.subTest(rota=rota):
                response = self.client.get(rota)
                self.assertEqual(response.status_code, 404)

    # -------------------------------------------------------------------------
    # Página inicial (/) — portão de entrada
    # -------------------------------------------------------------------------
    def test_index_redireciona_para_login(self):
        """Sem sessão: a raiz (/) leva direto à tela de login (ex-landing aposentada)."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/aluno/login', response.headers['Location'])


class SimuladoPdfPreview(unittest.TestCase):
    """Prévia navegável do PDF do simulado (navegador E app desktop).

    /simulado/<id>/pdf entrega SEMPRE a página navegável com o botão
    "Imprimir / Salvar PDF" — o padrão unificado dos resumos: no desktop
    (Electron) o botão gera PDF nativo via electronAPI.printToPDF(); no
    navegador, window.print() abre o preview de impressão nativo
    (Salvar como PDF). Não existe mais o PDF inline do WeasyPrint.
    """

    def setUp(self):
        """Inicializa o cliente de testes do Flask antes de cada teste."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    @patch('utils.current_user')
    @patch('rotas.simulado.current_user')
    @patch('rotas.simulado.safe_execute')
    @patch('rotas.simulado.supabase')
    def test_pdf_desktop_retorna_previa_navegavel(self, mock_supabase, mock_safe_execute, mock_rotas_cu, mock_utils_cu):
        """Com UA do app desktop, a rota devolve HTML navegável com botão nativo."""
        for u in (mock_rotas_cu, mock_utils_cu):
            u.is_authenticated = True
            u.role = 'aluno'

        res_simulado = MagicMock()
        res_simulado.data = {'id': '10955679-f9c8-4e55-b971-7bd0ff00bd99', 'titulo': 'Simulado de Teste'}
        res_sq = MagicMock()
        res_sq.data = [{'id_questao': 1}]
        res_questoes = MagicMock()
        res_questoes.data = [{'id_questao': 1, 'enunciado': 'Quanto é 2+2?', 'ano': 2026}]
        res_alts = MagicMock()
        res_alts.data = []
        mock_safe_execute.side_effect = [res_simulado, res_sq, res_questoes, res_alts]

        resposta = self.client.get(
            '/simulado/10955679-f9c8-4e55-b971-7bd0ff00bd99/pdf',
            headers={'User-Agent': 'Mozilla/5.0 GabariteiDesktop/1.0.1'},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b'Imprimir / Salvar PDF', resposta.data)
        self.assertIn(b'Gabarito Oficial', resposta.data)

    @patch('utils.current_user')
    @patch('rotas.simulado.current_user')
    @patch('rotas.simulado.safe_execute')
    @patch('rotas.simulado.supabase')
    def test_pdf_browser_retorna_previa_navegavel(self, mock_supabase, mock_safe_execute, mock_rotas_cu, mock_utils_cu):
        """Navegador (sem UA do app): a MESMA prévia navegável com o botão
        "Imprimir / Salvar PDF" — HTML navegável, nunca application/pdf inline."""
        for u in (mock_rotas_cu, mock_utils_cu):
            u.is_authenticated = True
            u.role = 'aluno'

        res_simulado = MagicMock()
        res_simulado.data = {'id': '10955679-f9c8-4e55-b971-7bd0ff00bd99', 'titulo': 'Simulado de Teste'}
        res_sq = MagicMock()
        res_sq.data = [{'id_questao': 1}]
        res_questoes = MagicMock()
        res_questoes.data = [{'id_questao': 1, 'enunciado': 'Quanto é 2+2?', 'ano': 2026}]
        res_alts = MagicMock()
        res_alts.data = []
        mock_safe_execute.side_effect = [res_simulado, res_sq, res_questoes, res_alts]

        resposta = self.client.get('/simulado/10955679-f9c8-4e55-b971-7bd0ff00bd99/pdf')
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b'Imprimir / Salvar PDF', resposta.data)
        self.assertIn('text/html', resposta.headers['Content-Type'])


if __name__ == '__main__':
    unittest.main()
