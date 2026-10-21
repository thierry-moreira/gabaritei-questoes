import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ['FLASK_ENV'] = 'development'
os.environ.setdefault('FLASK_SECRET_KEY', 'teste-chave-secreta-provisoria')

from app import app


def _sessao_auth_fake(user_email='aluno@teste.com'):
    s = MagicMock()
    s.user.id = 'uuid-teste-123'
    s.user.email = user_email
    s.refresh_token = 'refresh-teste'
    return s


def _linha_fake(uid=7):
    return {'id': uid, 'email': 'aluno@teste.com', 'username': 'Aluno Teste', 'role': 'aluno'}


class TestAuthComSenha(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def _flashes(self):
        with self.client.session_transaction() as sess:
            return [msg for _, msg in sess.get('_flashes', [])]

    # ------------------------------------------------------------------
    # Tela de login (GET /aluno/login)
    # ------------------------------------------------------------------
    def test_tela_login_sem_sessao_salva(self):
        """Sem refresh token salvo: mostra a tela de login com senha."""
        with patch('rotas.auth.sessao_atual', return_value=None):
            r = self.client.get('/aluno/login')
            self.assertEqual(r.status_code, 200)
            self.assertIn('Entrar na sua conta'.encode('utf-8'), r.data)

    def test_tela_login_restaura_sessao_salva(self):
        """Boot com refresh token salvo: restaura a sessão e vai ao painel."""
        with patch('rotas.auth.restaurar_sessao') as m_rest:
            with patch('rotas.auth._linha_do_usuario_auth', return_value=_linha_fake()):
                with patch('rotas.auth._entrar_flask') as m_entrar:
                    with self.client.session_transaction() as sess:
                        sess['auth_refresh_token'] = 'rt-salvo'
                    r = self.client.get('/aluno/login')
                    self.assertEqual(r.status_code, 302)
                    m_rest.assert_called_once_with('rt-salvo')
                    m_entrar.assert_called_once()

    def test_tela_login_refresh_invalido_mostra_tela(self):
        """Refresh expirado/revogado: limpa o token e mostra o login normal."""
        with patch('rotas.auth.restaurar_sessao', side_effect=Exception('expired')):
            with patch('rotas.auth.sair_auth') as m_sair:
                with self.client.session_transaction() as sess:
                    sess['auth_refresh_token'] = 'rt-velho'
                r = self.client.get('/aluno/login')
                self.assertEqual(r.status_code, 200)
                m_sair.assert_called_once()

    # ------------------------------------------------------------------
    # POST /aluno/entrar
    # ------------------------------------------------------------------
    @patch('rotas.auth._entrar_flask')
    @patch('rotas.auth._linha_do_usuario_auth', return_value=_linha_fake())
    @patch('rotas.auth.entrar_com_senha')
    def test_entrar_ok(self, m_login, m_linha, m_entrar_flask):
        """E-mail+senha corretos: entra e redireciona ao painel."""
        r = self.client.post('/aluno/entrar', data={'email': 'Aluno@Teste.com', 'senha': 'senha12345'})
        self.assertEqual(r.status_code, 302)
        m_login.assert_called_once_with('aluno@teste.com', 'senha12345')
        m_entrar_flask.assert_called_once()

    @patch('rotas.auth.entrar_com_senha', side_effect=Exception('Invalid login credentials'))
    def test_entrar_senha_errada(self, m_login):
        """Credenciais erradas: flash de erro e volta ao login."""
        r = self.client.post('/aluno/entrar', data={'email': 'a@b.com', 'senha': 'errada'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(any('incorretos' in m for m in self._flashes()))

    def test_entrar_campos_vazios(self):
        r = self.client.post('/aluno/entrar', data={'email': '', 'senha': ''})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(any('Informe e-mail e senha' in m for m in self._flashes()))

    # ------------------------------------------------------------------
    # POST /aluno/criar (cadastro)
    # ------------------------------------------------------------------
    def test_criar_senha_curta_bloqueia(self):
        """Senha < 8 caracteres: bloqueada antes de chamar o Auth."""
        with patch('rotas.auth.criar_conta_auth') as m_signup:
            r = self.client.post('/aluno/criar', data={'username': 'Aluno', 'email': 'a@b.com', 'senha': '123'})
            self.assertEqual(r.status_code, 302)
            m_signup.assert_not_called()
        self.assertTrue(any('mínimo' in m for m in self._flashes()))

    @patch('rotas.auth._entrar_flask')
    @patch('rotas.auth._criar_perfil', return_value=_linha_fake(9))
    @patch('rotas.auth.sessao_atual')
    @patch('rotas.auth.criar_conta_auth')
    def test_criar_ok(self, m_signup, m_sess, m_perfil, m_entrar):
        """Cadastro completo: cria conta Auth, perfil e entra."""
        m_sess.return_value = _sessao_auth_fake()
        r = self.client.post('/aluno/criar', data={'username': 'Novo Aluno', 'email': 'novo@teste.com', 'senha': 'senha12345'})
        self.assertEqual(r.status_code, 302)
        m_signup.assert_called_once_with('novo@teste.com', 'senha12345')
        m_perfil.assert_called_once_with('Novo Aluno', 'novo@teste.com')
        m_entrar.assert_called_once()

    @patch('rotas.auth.sessao_atual', return_value=None)
    @patch('rotas.auth.criar_conta_auth')
    def test_criar_aguardando_confirmacao_email(self, m_signup, m_sess):
        """'Confirm email' ligado no Auth: conta criada, sessão não — pede confirmação."""
        r = self.client.post('/aluno/criar', data={'username': 'Aluno', 'email': 'x@y.com', 'senha': 'senha12345'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(any('Confirme seu e-mail' in m for m in self._flashes()))

    @patch('rotas.auth.criar_conta_auth', side_effect=Exception('User already registered'))
    def test_criar_email_ja_existente(self, m_signup):
        """E-mail duplicado: avisa para logar ou recuperar a senha."""
        r = self.client.post('/aluno/criar', data={'username': 'Aluno', 'email': 'x@y.com', 'senha': 'senha12345'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(any('já tem conta' in m for m in self._flashes()))

    # ------------------------------------------------------------------
    # POST /aluno/esqueci
    # ------------------------------------------------------------------
    @patch('rotas.auth.pedir_reset_senha')
    def test_esqueci_dispara_reset(self, m_reset):
        """Dispara o e-mail de recuperação (e-mail normalizado em minúsculas)."""
        r = self.client.post('/aluno/esqueci', data={'email': 'A@Teste.com'})
        self.assertEqual(r.status_code, 302)
        m_reset.assert_called_once_with('a@teste.com')

    def test_esqueci_email_vazio(self):
        r = self.client.post('/aluno/esqueci', data={'email': ''})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(any('Informe seu e-mail' in m for m in self._flashes()))

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------
    @patch('rotas.auth.sair_auth')
    def test_logout_limpa_sessao_e_preserva_admin(self, m_sair):
        """Logout: limpa a sessão do aluno e preserva chaves admin_*."""
        with self.client.session_transaction() as sess:
            sess['admin_flag'] = 'preservar'
            sess['auth_refresh_token'] = 'rt-x'
        r = self.client.get('/logout')
        self.assertEqual(r.status_code, 302)
        m_sair.assert_called_once()
        with self.client.session_transaction() as sess:
            self.assertIn('admin_flag', sess)
            self.assertNotIn('auth_refresh_token', sess)


if __name__ == '__main__':
    unittest.main()