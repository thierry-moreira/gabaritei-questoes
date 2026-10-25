import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ['FLASK_ENV'] = 'development'
os.environ.setdefault('FLASK_SECRET_KEY', 'teste-chave-secreta-provisoria')

from app import app
from rotas import auth as rotas_auth
import banco_dados_aluno as bda


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

    @patch('rotas.auth.login_user')
    @patch('rotas.auth.sessao_atual', return_value=_sessao_auth_fake())
    @patch('rotas.auth._linha_do_usuario_auth', return_value=_linha_fake())
    @patch('rotas.auth.restaurar_sessao')
    def test_tela_login_persiste_novo_refresh_da_rotacao(self, m_rest, m_linha, m_sess, m_login_user):
        """Sessão eterna: boot com rt salvo grava o NOVO refresh token da rotação
        (o Supabase invalida o anterior a cada refresh) e deixa o cookie permanente."""
        with self.client.session_transaction() as sess:
            sess['auth_refresh_token'] = 'rt-salvo-antigo'
        r = self.client.get('/aluno/login')
        self.assertEqual(r.status_code, 302)
        m_rest.assert_called_once_with('rt-salvo-antigo')
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('auth_refresh_token'), 'refresh-teste',
                             'o NOVO token da rotação deve substituir o antigo')
            self.assertTrue(sess.get('_permanent'),
                            'cookie deve ser permanente (sobrevive ao Electron fechar)')

    # ------------------------------------------------------------------
    # Sessão eterna do desktop — before_request do app.py
    # ------------------------------------------------------------------
    @patch('app._sessao_auth_atual')
    @patch('app._restaurar_sessao_auth')
    def test_before_request_persiste_novo_refresh(self, m_restaurar, m_sessao):
        """Client anônimo (boot novo): reaplica o rt do cookie e grava o NOVO.

        Regressão do bug do 302 no /simulado/<id>/pdf: a guarda do
        before_request NÃO pode ser current_user.is_authenticated (o
        acesso ao proxy dispara o load_user ANTES da restauração; com
        client anônimo o RLS filtra o perfil, load_user=None e a
        restauração nunca rodava). A guarda é o _user_id da sessão Flask
        — a mesma chave que o Flask-Login usa para chamar o user_loader."""
        m_sessao.side_effect = [None, _sessao_auth_fake()]
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '50'
            sess['auth_refresh_token'] = 'rt-velho'
        self.client.get('/aluno/login')
        m_restaurar.assert_called_once_with('rt-velho')
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('auth_refresh_token'), 'refresh-teste')
            self.assertTrue(sess.get('_permanent'))

    @patch('app._sessao_auth_atual')
    @patch('app._restaurar_sessao_auth')
    def test_before_request_renova_access_token_a_expirar(self, m_restaurar, m_sessao):
        """Renovação proativa: access token a expirar (<2 min) é renovado ANTES de falhar,
        com o novo refresh token persistido na sessão."""
        import time as _t
        s_expirando = _sessao_auth_fake()
        s_expirando.expires_at = _t.time() + 60
        m_sessao.side_effect = [s_expirando, _sessao_auth_fake()]
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '50'
            sess['auth_refresh_token'] = 'rt-velho'
        self.client.get('/aluno/login')
        m_restaurar.assert_called_once_with('rt-velho')
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('auth_refresh_token'), 'refresh-teste')

    @patch('app._sessao_auth_atual')
    @patch('app._restaurar_sessao_auth')
    def test_before_request_anonimo_nao_restaura(self, m_restaurar, m_sessao):
        """Sessão SEM _user_id (deslogado): o before_request não restaura
        nem consulta o client Auth (princípio do menor privilégio)."""
        with self.client.session_transaction() as sess:
            sess['auth_refresh_token'] = 'rt-orfao'  # sem _user_id na sessão
        r = self.client.get('/static/js/imprimir_ou_pdf.js')
        self.assertEqual(r.status_code, 200)
        m_restaurar.assert_not_called()
        m_sessao.assert_not_called()

    # ------------------------------------------------------------------
    # Self-heal do load_user (perfil invisível = client morto → restaura)
    # ------------------------------------------------------------------
    @patch('app._sessao_auth_atual')
    @patch('app._restaurar_sessao_auth')
    @patch('app.supabase')
    def test_load_user_self_heal_restaura_e_reconsulta(self, m_sb, m_restaurar, m_sessao):
        """Regressão do 302: consulta do perfil vazia (client anônimo/token
        morto — o RLS filtra as linhas) → load_user restaura pelo refresh
        token da sessão, persiste o NOVO da rotação e reconsulta; o usuário
        logado NÃO pode virar 'deslogado' no 1º request pós-boot."""
        from app import load_user
        from flask import session as flask_session
        m_sessao.return_value = _sessao_auth_fake()

        res_vazia = MagicMock()
        res_vazia.data = []
        res_ok = MagicMock()
        res_ok.data = [_linha_fake(50)]
        m_sb.table.return_value.select.return_value.eq.return_value.execute.side_effect = [res_vazia, res_ok]

        with patch.dict(app.config, {'TESTING': False}):
            with app.test_request_context('/'):
                flask_session['auth_refresh_token'] = 'rt-morto'
                u = load_user('50')

                self.assertIsNotNone(u)
                self.assertEqual(u.id, 50)
                m_restaurar.assert_called_once_with('rt-morto')
                self.assertEqual(flask_session.get('auth_refresh_token'), 'refresh-teste')
                self.assertTrue(flask_session.get('_permanent'))

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

    @patch('rotas.auth.login_user')
    @patch('rotas.auth.sessao_atual', return_value=_sessao_auth_fake())
    @patch('rotas.auth._linha_do_usuario_auth', return_value=_linha_fake())
    @patch('rotas.auth.entrar_com_senha')
    def test_entrar_deixa_sessao_permanente_e_salva_refresh(self, m_login_auth, m_linha, m_sess, m_login_user):
        """Sessão eterna: login com senha grava cookie permanente + refresh token
        (o _entrar_flask roda REAL — é ele quem persiste o token e a permanência)."""
        r = self.client.post('/aluno/entrar', data={'email': 'aluno@teste.com', 'senha': 'senha12345'})
        self.assertEqual(r.status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertTrue(sess.get('_permanent'), 'cookie deve ser permanente')
            self.assertEqual(sess.get('auth_refresh_token'), 'refresh-teste')
        m_login_user.assert_called_once()

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

    @patch('rotas.auth._entrar_flask')
    @patch('rotas.auth._criar_perfil', return_value=_linha_fake(9))
    @patch('rotas.auth._linha_do_usuario_auth', return_value=None)
    @patch('rotas.auth.entrar_com_senha')
    def test_entrar_sem_perfil_cria_e_entra(self, m_login, m_linha, m_perfil, m_entrar):
        """Conta Auth ok mas sem perfil (ex.: legado): cria/re-linka e entra."""
        r = self.client.post('/aluno/entrar', data={'email': 'legado@teste.com', 'senha': 'senha12345'})
        self.assertEqual(r.status_code, 302)
        m_perfil.assert_called_once_with('legado', 'legado@teste.com')
        m_entrar.assert_called_once()

    # ------------------------------------------------------------------
    # _criar_perfil: re-link de perfil legado + fallback de username
    # ------------------------------------------------------------------
    def test_criar_perfil_relink_legado(self):
        """Perfil legado (auth_id NULL) de mesmo e-mail: adota em vez de duplicar."""
        legado = _linha_fake(50)
        with patch('rotas.auth.sessao_atual', return_value=_sessao_auth_fake()):
            with patch('rotas.auth.supabase') as m_sb:
                m_sb.table.return_value.update.return_value.is_.return_value.execute.return_value = MagicMock(data=[legado])
                linha = rotas_auth._criar_perfil('Novo', 'aluno@teste.com')
        self.assertEqual(linha, legado)
        m_sb.table.return_value.update.assert_called_once_with({'auth_id': 'uuid-teste-123'})
        m_sb.table.return_value.insert.assert_not_called()

    def test_criar_perfil_sem_legado_insere(self):
        """Sem perfil legado: insere linha nova com auth_id do JWT."""
        nova = _linha_fake(99)
        with patch('rotas.auth.sessao_atual', return_value=_sessao_auth_fake()):
            with patch('rotas.auth.supabase') as m_sb:
                m_sb.table.return_value.update.return_value.is_.return_value.execute.return_value = MagicMock(data=[])
                m_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[nova])
                linha = rotas_auth._criar_perfil('Novo', 'novo@teste.com')
        self.assertEqual(linha, nova)
        inserido = m_sb.table.return_value.insert.call_args[0][0]
        self.assertEqual(inserido['auth_id'], 'uuid-teste-123')
        self.assertEqual(inserido['username'], 'Novo')

    def test_criar_perfil_username_ocupado_tenta_sufixo(self):
        """Colisão de username (23505): segunda tentativa usa sufixo _hex (padrão legado)."""
        nova = _linha_fake(98)
        with patch('rotas.auth.sessao_atual', return_value=_sessao_auth_fake()):
            with patch('rotas.auth.supabase') as m_sb:
                m_sb.table.return_value.update.return_value.is_.return_value.execute.return_value = MagicMock(data=[])
                m_sb.table.return_value.insert.return_value.execute.side_effect = [
                    Exception("{'message': 'duplicate key value violates unique constraint \"usuarios_username_key\"', 'code': '23505'}"),
                    MagicMock(data=[nova]),
                ]
                linha = rotas_auth._criar_perfil('Novo', 'novo@teste.com')
        self.assertEqual(linha, nova)
        self.assertEqual(m_sb.table.return_value.insert.call_count, 2)
        segundo = m_sb.table.return_value.insert.call_args_list[1][0][0]
        self.assertTrue(segundo['username'].startswith('Novo_'))

    def test_criar_perfil_falha_persisvel_retorna_none(self):
        """Falha não-recuperável no INSERT: sem exceção propagada — flash amigável."""
        with patch('rotas.auth.sessao_atual', return_value=_sessao_auth_fake()):
            with patch('rotas.auth.supabase') as m_sb:
                m_sb.table.return_value.update.return_value.is_.return_value.execute.return_value = MagicMock(data=[])
                m_sb.table.return_value.insert.return_value.execute.side_effect = Exception("{'code': '42501', 'message': 'new row violates row-level security policy'}")
                linha = rotas_auth._criar_perfil('Novo', 'novo@teste.com')
        self.assertIsNone(linha)


    # ------------------------------------------------------------------
    # POST /aluno/criar (cadastro)
    # ------------------------------------------------------------------
    def test_criar_senha_curta_bloqueia(self):
        """Senha < 8 caracteres: bloqueada antes de chamar o Auth."""
        with patch('rotas.auth.criar_conta_auth') as m_signup:
            r = self.client.post('/aluno/criar', data={'username': 'Aluno', 'email': 'a@b.com', 'senha': '123', 'confirmar_senha': '123'})
            self.assertEqual(r.status_code, 302)
            m_signup.assert_not_called()
        self.assertTrue(any('mínimo' in m for m in self._flashes()))

    @patch('rotas.auth.criar_conta_auth')
    def test_criar_senhas_diferentes_bloqueia(self, m_signup):
        """Senha e confirmação diferentes: bloqueada antes de chamar o Auth."""
        r = self.client.post('/aluno/criar', data={'username': 'Aluno', 'email': 'a@b.com', 'senha': 'senha12345', 'confirmar_senha': 'outra12345'})
        self.assertEqual(r.status_code, 302)
        m_signup.assert_not_called()
        self.assertTrue(any('não conferem' in m for m in self._flashes()))

    @patch('rotas.auth._entrar_flask')
    @patch('rotas.auth._criar_perfil', return_value=_linha_fake(9))
    @patch('rotas.auth.sessao_atual')
    @patch('rotas.auth.criar_conta_auth')
    def test_criar_ok(self, m_signup, m_sess, m_perfil, m_entrar):
        """Cadastro completo: cria conta Auth, perfil e entra."""
        m_sess.return_value = _sessao_auth_fake()
        r = self.client.post('/aluno/criar', data={'username': 'Novo Aluno', 'email': 'novo@teste.com', 'senha': 'senha12345', 'confirmar_senha': 'senha12345'})
        self.assertEqual(r.status_code, 302)
        m_signup.assert_called_once_with('novo@teste.com', 'senha12345')
        m_perfil.assert_called_once_with('Novo Aluno', 'novo@teste.com')
        m_entrar.assert_called_once()

    @patch('rotas.auth.sessao_atual', return_value=None)
    @patch('rotas.auth.criar_conta_auth')
    def test_criar_aguardando_confirmacao_email(self, m_signup, m_sess):
        """'Confirm email' ligado no Auth: conta criada, sessão não — pede confirmação."""
        r = self.client.post('/aluno/criar', data={'username': 'Aluno', 'email': 'x@y.com', 'senha': 'senha12345', 'confirmar_senha': 'senha12345'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(any('Confirme seu e-mail' in m for m in self._flashes()))

    @patch('rotas.auth.criar_conta_auth', side_effect=Exception('User already registered'))
    def test_criar_email_ja_existente(self, m_signup):
        """E-mail duplicado: avisa para logar ou recuperar a senha."""
        r = self.client.post('/aluno/criar', data={'username': 'Aluno', 'email': 'x@y.com', 'senha': 'senha12345', 'confirmar_senha': 'senha12345'})
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

    # ------------------------------------------------------------------
    # E-mails do Auth → página pública de confirmação (GitHub Pages)
    # ------------------------------------------------------------------
    def test_emails_auth_redirecionam_para_pagina_publica(self):
        """Signup e recuperação apontam os links dos e-mails para a página pública."""
        self.assertTrue(bda.URL_POS_EMAIL.startswith('https://thierry-moreira.github.io/'))
        with patch('banco_dados_aluno.supabase') as m_sb:
            bda.criar_conta_auth('a@b.com', 'senha12345')
            m_sb.auth.sign_up.assert_called_once_with({
                'email': 'a@b.com',
                'password': 'senha12345',
                'options': {'email_redirect_to': bda.URL_POS_EMAIL},
            })
            bda.pedir_reset_senha('a@b.com')
            m_sb.auth.reset_password_for_email.assert_called_once_with(
                'a@b.com', options={'redirect_to': bda.URL_POS_EMAIL})


if __name__ == '__main__':
    unittest.main()