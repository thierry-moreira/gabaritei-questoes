# -*- coding: utf-8 -*-
"""
Testes da camada BYOK de IA (provedores_ia.py) e do banco local
(banco_local.py). 100% isolados: nenhuma chamada de rede real — todos os
pings e SDKs são mockados; o SQLite usa tmpdir via GABARITEI_LOCAL_DIR.

No Windows, o roundtrip do banco local exercita a DPAPI REAL (o mesmo
usuário do dev cifra/decifra — comportamento idêntico ao de produção).
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ.setdefault('FLASK_SECRET_KEY', 'teste-chave-ia-provedores')

import banco_local
from provedores_ia import (
    PROVEDORES, TEMPERATURE_GPT, ErroIA,
    chamar_ia, ia_configurada, testar_chave, _filtrar_parametros,
)


class TestBancoLocal(unittest.TestCase):
    """Roundtrip do banco local (SQLite + DPAPI real no Windows) em tmpdir."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ['GABARITEI_LOCAL_DIR'] = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()
        os.environ.pop('GABARITEI_LOCAL_DIR', None)

    def test_roundtrip_salvar_ler_remover(self):
        banco_local.salvar_config_ia(1, 'openai', 'gpt-5.6-luna', 'sk-teste-1111')
        cfg = banco_local.ler_config_ia(1)
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg['provedor'], 'openai')
        self.assertEqual(cfg['modelo'], 'gpt-5.6-luna')
        self.assertEqual(cfg['chave'], 'sk-teste-1111')
        self.assertTrue(banco_local.remover_config_ia(1))
        self.assertIsNone(banco_local.ler_config_ia(1))

    def test_isolamento_por_usuario(self):
        """Multiusuário na mesma máquina: cada conta tem sua própria config."""
        banco_local.salvar_config_ia(1, 'openai', 'gpt-5.6-luna', 'sk-aluno-um')
        banco_local.salvar_config_ia(2, 'gemini', 'gemini-4-argon', 'gk-aluno-dois')
        self.assertEqual(banco_local.ler_config_ia(1)['chave'], 'sk-aluno-um')
        self.assertEqual(banco_local.ler_config_ia(2)['chave'], 'gk-aluno-dois')
        self.assertIsNone(banco_local.ler_config_ia(3))

    def test_mascarar_chave(self):
        self.assertEqual(banco_local.mascarar_chave('sk-1111222233334444'), 'sk-1…4444')
        self.assertEqual(banco_local.mascarar_chave(''), '')
        self.assertEqual(banco_local.mascarar_chave('123'), '••••••')

    def test_chave_nunca_em_texto_plano_no_arquivo(self):
        """O SQLite nunca guarda a chave em plaintext (DPAPI/base64)."""
        banco_local.salvar_config_ia(7, 'anthropic', 'claude-sonnet-5-5', 'sk-ant-SECRETA-9999')
        with open(str(banco_local._caminho_banco()), 'r', encoding='utf-8', errors='ignore') as f:
            conteudo = f.read()
        self.assertNotIn('sk-ant-SECRETA-9999', conteudo)


class TestListasOficiais(unittest.TestCase):
    """Regressão das listas de modelos aprovadas pelo produto (congeladas)."""

    def test_modelos_openai(self):
        self.assertEqual(PROVEDORES['openai']['modelos'], [
            'gpt-6.1-sol', 'gpt-5.6-luna', 'gpt-5.6-terra', 'gpt-6-sol',
            'gpt-5.2-2025-12-11', 'gpt-5-2025-08-07', 'gpt-5.4-2026-03-05',
        ])
        self.assertEqual(PROVEDORES['openai']['modelo_padrao'], 'gpt-5.6-luna')

    def test_modelos_gemini(self):
        self.assertEqual(PROVEDORES['gemini']['modelos'], [
            'gemini-4-argon', 'gemini-3.8-flash', 'gemini-3.1-pro-preview',
            'gemini-3.5-flash-lite',
        ])
        self.assertEqual(PROVEDORES['gemini']['modelo_padrao'], 'gemini-4-argon')

    def test_modelos_anthropic(self):
        self.assertEqual(PROVEDORES['anthropic']['modelos'], ['claude-haiku-5-5', 'claude-sonnet-5-5'])
        self.assertEqual(PROVEDORES['anthropic']['modelo_padrao'], 'claude-sonnet-5-5')

    def test_temperatura_congelada(self):
        """TEMPERATURE_GPT herdada de extensoes.py — valor calibrado do produto."""
        self.assertEqual(TEMPERATURE_GPT, 0.3)

    def test_todos_os_padroes_estao_nas_listas(self):
        for slug, dados in PROVEDORES.items():
            self.assertIn(
                dados['modelo_padrao'], dados['modelos'],
                f"modelo_padrao de '{slug}' fora da lista oficial",
            )


class TestCamadaBYOK(unittest.TestCase):
    """Dispatch da chamar_ia por provedor — tudo mockado, zero rede."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ['GABARITEI_LOCAL_DIR'] = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()
        os.environ.pop('GABARITEI_LOCAL_DIR', None)

    def _configurar(self, provedor, modelo='gpt-5.6-luna'):
        banco_local.salvar_config_ia(42, provedor, modelo, 'sk-chave-de-teste-123456')

    def test_sem_config_levanta_erro_amigavel(self):
        with self.assertRaises(ErroIA) as ctx:
            chamar_ia(42, 'system', [{'type': 'text', 'text': 'oi'}], temperature=0.3)
        self.assertEqual(ctx.exception.codigo, 'sem_config')

    @patch('provedores_ia.OpenAI')
    def test_dispatch_openai_role_developer(self, mock_sdk):
        """OpenAI: role 'developer' + todos os parâmetros calibrados passam."""
        self._configurar('openai')
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = 'resposta openai'
        mock_sdk.return_value.chat.completions.create.return_value = mock_resp

        texto = chamar_ia(42, 'prompt sys', [{'type': 'text', 'text': 'enunciado'}],
                          temperature=0.0, top_p=0.1, presence_penalty=0.0, frequency_penalty=0.0)

        self.assertEqual(texto, 'resposta openai')
        kwargs = mock_sdk.return_value.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs['model'], 'gpt-5.6-luna')
        self.assertEqual(kwargs['messages'][0]['role'], 'developer')
        self.assertEqual(kwargs['temperature'], 0.0)
        self.assertEqual(kwargs['top_p'], 0.1)
        self.assertEqual(kwargs['presence_penalty'], 0.0)
        self.assertEqual(kwargs['frequency_penalty'], 0.0)

    @patch('provedores_ia.OpenAI')
    def test_dispatch_gemini_base_url_google_e_role_system(self, mock_sdk):
        """Gemini: endpoint OpenAI-compat do Google + role 'system'."""
        self._configurar('gemini', 'gemini-4-argon')
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = 'resposta gemini'
        mock_sdk.return_value.chat.completions.create.return_value = mock_resp

        texto = chamar_ia(42, 'prompt sys', [{'type': 'text', 'text': 'enunciado'}], temperature=0.3)

        self.assertEqual(texto, 'resposta gemini')
        self.assertIn(
            'generativelanguage.googleapis.com',
            str(mock_sdk.call_args.kwargs.get('base_url', '')),
        )
        kwargs = mock_sdk.return_value.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs['model'], 'gemini-4-argon')
        self.assertEqual(kwargs['messages'][0]['role'], 'system')
        self.assertEqual(kwargs['temperature'], 0.3)

    @patch('provedores_ia.requests.post')
    def test_dispatch_anthropic_payload_nativo(self, mock_post):
        """Anthropic: Messages API nativa; penalties não suportados são omitidos."""
        self._configurar('anthropic', 'claude-sonnet-5-5')
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'content': [{'type': 'text', 'text': 'resposta claude'}]
        }

        texto = chamar_ia(42, 'prompt sys', [{'type': 'text', 'text': 'enunciado'}],
                          temperature=0.3, presence_penalty=0.0, frequency_penalty=0.0)

        self.assertEqual(texto, 'resposta claude')
        args, kwargs = mock_post.call_args
        self.assertIn('/v1/messages', args[0])
        payload = kwargs['json']
        self.assertEqual(payload['model'], 'claude-sonnet-5-5')
        self.assertEqual(payload['system'], 'prompt sys')
        self.assertEqual(payload['temperature'], 0.3)
        self.assertNotIn('presence_penalty', payload)
        self.assertNotIn('frequency_penalty', payload)
        self.assertEqual(kwargs['headers']['x-api-key'], 'sk-chave-de-teste-123456')

    @patch('provedores_ia.requests.post')
    def test_dispatch_anthropic_chave_invalida(self, mock_post):
        self._configurar('anthropic')
        mock_post.return_value.status_code = 401
        with self.assertRaises(ErroIA) as ctx:
            chamar_ia(42, 'sys', [{'type': 'text', 'text': 'oi'}], temperature=0.3)
        self.assertEqual(ctx.exception.codigo, 'chave_invalida')

    @patch('provedores_ia.requests.post')
    def test_dispatch_anthropic_sem_creditos_402(self, mock_post):
        """402 billing_error → mensagem clara (a API da Anthropic exige créditos
        ativos; não há free tier com chave)."""
        self._configurar('anthropic')
        mock_post.return_value.status_code = 402
        with self.assertRaises(ErroIA) as ctx:
            chamar_ia(42, 'sys', [{'type': 'text', 'text': 'oi'}], temperature=0.3)
        self.assertEqual(ctx.exception.codigo, 'sem_credito')

    def test_filtrar_parametros_anthropic(self):
        params = _filtrar_parametros('anthropic', {
            'temperature': 0.3, 'top_p': 0.9,
            'presence_penalty': 0.0, 'frequency_penalty': 0.0,
        })
        self.assertEqual(sorted(params), ['temperature', 'top_p'])

    def test_ia_configurada(self):
        self.assertFalse(ia_configurada(42))
        self._configurar('openai')
        self.assertTrue(ia_configurada(42))


class TestRetryParametrosNaoSuportados(unittest.TestCase):
    """Modelos de raciocínio (família gpt-5/6) rejeitam sampling: a camada
    remove o parâmetro indicado pela API e repete — mantendo os calibrados
    sempre na primeira tentativa."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ['GABARITEI_LOCAL_DIR'] = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()
        os.environ.pop('GABARITEI_LOCAL_DIR', None)

    @patch('provedores_ia.OpenAI')
    def test_modelo_rejeita_temperature_e_repete_sem(self, mock_sdk):
        """400 'unsupported_value' em temperature → retry sem ela; a 1ª chamada
        presencia os parâmetros calibrados (congelamento intacto)."""
        from openai import BadRequestError
        banco_local.salvar_config_ia(42, 'openai', 'gpt-5.6-luna', 'sk-chave-de-teste-123456')

        erro = BadRequestError(
            message="Error code: 400 - {'error': {'message': \"Unsupported value: 'temperature' does not support 0.0 with this model. Only the default (1) value is supported.\", 'type': 'invalid_request_error', 'param': 'temperature', 'code': 'unsupported_value'}}",
            response=MagicMock(),
            body={'error': {
                'message': "Unsupported value: 'temperature' does not support 0.0 with this model.",
                'type': 'invalid_request_error', 'param': 'temperature', 'code': 'unsupported_value',
            }},
        )
        ok = MagicMock()
        ok.choices[0].message.content = 'explicacao ok'
        mock_sdk.return_value.chat.completions.create.side_effect = [erro, ok]

        texto = chamar_ia(42, 'sys', [{'type': 'text', 'text': 'q'}],
                          temperature=0.0, top_p=0.1, presence_penalty=0.0, frequency_penalty=0.0)

        self.assertEqual(texto, 'explicacao ok')
        chamadas = mock_sdk.return_value.chat.completions.create.call_args_list
        self.assertEqual(len(chamadas), 2)
        # 1ª tentativa: parâmetros calibrados ENVIADOS (congelamento)
        self.assertEqual(chamadas[0].kwargs['temperature'], 0.0)
        self.assertEqual(chamadas[0].kwargs['top_p'], 0.1)
        # 2ª tentativa: sem o parâmetro rejeitado; os demais permanecem
        self.assertNotIn('temperature', chamadas[1].kwargs)
        self.assertEqual(chamadas[1].kwargs['top_p'], 0.1)

    @patch('provedores_ia.OpenAI')
    def test_erro_400_sem_param_conhecido_propaga_sem_loop(self, mock_sdk):
        """400 sem param reconhecido não gera retry infinito: propaga direto."""
        from openai import BadRequestError
        banco_local.salvar_config_ia(42, 'openai', 'gpt-5.6-luna', 'sk-chave-de-teste-123456')

        erro = BadRequestError(
            message="Error code: 400 - {'error': {'message': 'Erro qualquer', 'type': 'invalid_request_error', 'code': 'invalid_format'}}",
            response=MagicMock(),
            body={'error': {'message': 'Erro qualquer', 'type': 'invalid_request_error',
                            'code': 'invalid_format'}},
        )
        mock_sdk.return_value.chat.completions.create.side_effect = erro

        with self.assertRaises(BadRequestError):
            chamar_ia(42, 'sys', [{'type': 'text', 'text': 'q'}], temperature=0.3)
        self.assertEqual(mock_sdk.return_value.chat.completions.create.call_count, 1)

    @patch('provedores_ia.requests.post')
    def test_anthropic_400_com_param_repete_sem(self, mock_post):
        """Mesma guarda defensiva no caminho REST da Anthropic."""
        banco_local.salvar_config_ia(42, 'anthropic', 'claude-sonnet-5-5', 'sk-chave-de-teste-123456')

        r400 = MagicMock()
        r400.status_code = 400
        r400.json.return_value = {'type': 'error', 'error': {
            'type': 'invalid_request_error',
            'message': 'temperature unsupported for this model',
            'param': 'temperature',
        }}
        r200 = MagicMock()
        r200.status_code = 200
        r200.json.return_value = {'content': [{'type': 'text', 'text': 'ok claude'}]}
        mock_post.side_effect = [r400, r200]

        texto = chamar_ia(42, 'sys', [{'type': 'text', 'text': 'q'}], temperature=0.3)

        self.assertEqual(texto, 'ok claude')
        self.assertEqual(mock_post.call_count, 2)
        self.assertNotIn('temperature', mock_post.call_args_list[1].kwargs['json'])

    @patch('provedores_ia.OpenAI')
    def test_gemini_penalties_omitidos_estaticamente(self, mock_sdk):
        """O compat endpoint do Gemini rejeita presence/frequency_penalty
        (400 'Unknown name'): eles são omitidos ANTES da 1ª chamada."""
        banco_local.salvar_config_ia(42, 'gemini', 'gemini-3.5-flash-lite', 'sk-chave-de-teste-123456')
        ok = MagicMock()
        ok.choices[0].message.content = 'ok gemini'
        mock_sdk.return_value.chat.completions.create.return_value = ok

        chamar_ia(42, 'sys', [{'type': 'text', 'text': 'q'}],
                  temperature=0.0, top_p=0.1, presence_penalty=0.0, frequency_penalty=0.0)

        kwargs = mock_sdk.return_value.chat.completions.create.call_args.kwargs
        self.assertNotIn('presence_penalty', kwargs)
        self.assertNotIn('frequency_penalty', kwargs)
        self.assertEqual(kwargs['temperature'], 0.0)   # temperature/top_p preservados
        self.assertEqual(kwargs['top_p'], 0.1)
        self.assertEqual(mock_sdk.return_value.chat.completions.create.call_count, 1)

    @patch('provedores_ia.OpenAI')
    def test_gemini_erro_formato_google_repete_sem_param(self, mock_sdk):
        """400 do Google (INVALID_ARGUMENT / fieldViolations) também dispara o
        retry: 1ª chamada com o parâmetro, 2ª sem."""
        from openai import BadRequestError
        banco_local.salvar_config_ia(42, 'gemini', 'gemini-4-argon', 'sk-chave-de-teste-123456')

        msg_google = 'Invalid JSON payload received. Unknown name "temperature": Cannot find field.'
        erro = BadRequestError(
            message="Error code: 400 - [{'error': {'code': 400, 'message': '%s', 'status': 'INVALID_ARGUMENT'}}]" % msg_google,
            response=MagicMock(),
            body={'error': {'code': 400, 'message': msg_google, 'status': 'INVALID_ARGUMENT',
                            'details': [{'@type': 'type.googleapis.com/google.rpc.BadRequest',
                                         'fieldViolations': [{'description': msg_google}]}]}},
        )
        ok = MagicMock()
        ok.choices[0].message.content = 'resposta gemini'
        mock_sdk.return_value.chat.completions.create.side_effect = [erro, ok]

        texto = chamar_ia(42, 'sys', [{'type': 'text', 'text': 'q'}], temperature=0.3, top_p=0.9)

        self.assertEqual(texto, 'resposta gemini')
        chamadas = mock_sdk.return_value.chat.completions.create.call_args_list
        self.assertEqual(len(chamadas), 2)
        self.assertEqual(chamadas[0].kwargs['temperature'], 0.3)
        self.assertNotIn('temperature', chamadas[1].kwargs)


class TestValidarChave(unittest.TestCase):
    """testar_chave: pings GET gratuitos — todos mockados, zero rede."""

    def _resposta(self, status):
        r = MagicMock()
        r.status_code = status
        return r

    @patch('provedores_ia.requests.get')
    def test_ping_401_chave_invalida(self, mock_get):
        mock_get.return_value = self._resposta(401)
        ok, motivo = testar_chave('openai', 'sk-' + '1' * 40, 'gpt-5.6-luna')
        self.assertFalse(ok)
        self.assertIn('Chave de API inválida', motivo)

    @patch('provedores_ia.requests.get')
    def test_ping_404_modelo_invalido(self, mock_get):
        mock_get.side_effect = [self._resposta(200), self._resposta(404)]
        ok, motivo = testar_chave('openai', 'sk-' + '1' * 40, 'modelo-fantasma')
        self.assertFalse(ok)
        self.assertIn('Modelo não encontrado', motivo)

    @patch('provedores_ia.requests.get')
    def test_ping_402_sem_creditos(self, mock_get):
        """402 billing_error (Anthropic sem créditos) → motivo claro de crédito."""
        mock_get.side_effect = [self._resposta(402), self._resposta(402)]
        ok, motivo = testar_chave('anthropic', 'sk-ant-' + '1' * 40, 'claude-sonnet-5-5')
        self.assertFalse(ok)
        self.assertIn('créditos', motivo)

    @patch('provedores_ia.requests.get')
    def test_ping_sucesso(self, mock_get):
        mock_get.side_effect = [self._resposta(200), self._resposta(200)]
        ok, motivo = testar_chave('anthropic', 'sk-ant-' + '1' * 40, 'claude-sonnet-5-5')
        self.assertTrue(ok)
        self.assertEqual(motivo, '')

    def test_provedor_desconhecido(self):
        ok, motivo = testar_chave('inexistente', 'chave', 'modelo')
        self.assertFalse(ok)
        self.assertIn('Provedor não suportado', motivo)


if __name__ == '__main__':
    unittest.main()
