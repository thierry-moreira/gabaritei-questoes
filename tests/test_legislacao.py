import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configura o ambiente de testes
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'teste-chave-secreta-legislacao')

import legislacao
from legislacao import (
    limpar_html,
    recuperar_legislacao,
    montar_bloco_contexto,
    montar_evidencia,
    MAX_TEXTO_TRECHO,
)


class TestLimparHtml(unittest.TestCase):
    """Sanitização do enunciado antes da busca lexical (FTS limpa)."""

    def test_remove_tags_e_entidades(self):
        # Tags viram espaço (evita colar palavras de blocos adjacentes);
        # o espaço extra antes de pontuação é inofensivo — o texto serve
        # de consulta FTS, onde o parser ignora pontuação.
        texto = '<p>O servidor&nbsp;aceita <b>propina</b>?</p>'
        self.assertEqual(limpar_html(texto), 'O servidor aceita propina ?')

    def test_normaliza_espacos_e_none(self):
        self.assertEqual(limpar_html('  a \n\t b  '), 'a b')
        self.assertEqual(limpar_html(None), '')


class TestRecuperarLegislacao(unittest.TestCase):

    def test_recupera_trechos_normalizados(self):
        with patch('legislacao.supabase') as mock_supabase:
            res = MagicMock()
            res.data = [{
                'id': 42,
                'referencia': 'Lei nº 8.112/1990 — art. 117, inciso IX',
                'texto': 'Aceitar propina.',
                'vigencia_de': '1990-01-08',
                'vigencia_ate': None,
            }]
            mock_supabase.rpc.return_value.execute.return_value = res

            trechos = recuperar_legislacao(7, 9, 'Servidor aceita propina?')

        self.assertEqual(len(trechos), 1)
        self.assertEqual(trechos[0]['id'], 42)
        self.assertEqual(trechos[0]['vigencia_ate'], None)
        # Taxonomia da questão vira filtro estruturado da RPC
        mock_supabase.rpc.assert_called_once_with('buscar_legislacao', {
            'p_texto': 'Servidor aceita propina?',
            'p_limite': 5,
            'p_id_materia': 7,
            'p_id_topico': 9,
        })

    def test_fail_open_quando_rpc_falha(self):
        """RPC inexistente/rede fora → lista vazia, nunca exceção (contrato fail-open)."""
        with patch('legislacao.supabase') as mock_supabase:
            mock_supabase.rpc.return_value.execute.side_effect = Exception('PGRST202 function not found')
            self.assertEqual(recuperar_legislacao(1, None, 'Enunciado longo o suficiente aqui.'), [])

    def test_enunciado_curto_nao_busca(self):
        with patch('legislacao.supabase') as mock_supabase:
            self.assertEqual(recuperar_legislacao(None, None, 'Curto'), [])
            mock_supabase.rpc.assert_not_called()

    def test_texto_longo_e_truncado(self):
        with patch('legislacao.supabase') as mock_supabase:
            res = MagicMock()
            res.data = [{'id': 1, 'referencia': 'Lei X', 'texto': 'a' * (MAX_TEXTO_TRECHO + 500)}]
            mock_supabase.rpc.return_value.execute.return_value = res

            trechos = recuperar_legislacao(None, None, 'Enunciado longo o suficiente para buscar.')

        self.assertTrue(trechos[0]['texto'].endswith(' …'))
        self.assertLessEqual(len(trechos[0]['texto']), MAX_TEXTO_TRECHO + 2)  # + sufixo " …"

    def test_linhas_sem_texto_sao_ignoradas(self):
        with patch('legislacao.supabase') as mock_supabase:
            res = MagicMock()
            res.data = [{'id': 1, 'referencia': 'Lei X', 'texto': None}, 'lixo', None]
            mock_supabase.rpc.return_value.execute.return_value = res

            self.assertEqual(recuperar_legislacao(None, None, 'Enunciado longo o suficiente para buscar.'), [])

    def test_limite_e_limitado_ao_padrao(self):
        with patch('legislacao.supabase') as mock_supabase:
            mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=[])
            recuperar_legislacao(None, None, 'Enunciado longo o suficiente para buscar.', limite=99)
        self.assertEqual(mock_supabase.rpc.call_args.args[1]['p_limite'], legislacao.LIMITE_PADRAO)


class TestMontarBlocoContexto(unittest.TestCase):

    def test_vazio_retorna_string_vazia(self):
        self.assertEqual(montar_bloco_contexto([]), '')

    def test_formato_com_vigencia_encerrada(self):
        bloco = montar_bloco_contexto([{
            'id': 1, 'referencia': 'CLT — art. 443',
            'texto': 'O contrato de trabalho por prazo determinado...', 'vigencia_de': '1943-05-01', 'vigencia_ate': '2025-12-31'
        }])
        self.assertIn('[1] CLT — art. 443', bloco)
        self.assertIn('VIGÊNCIA ENCERRADA em 2025-12-31', bloco)
        self.assertIn('O contrato de trabalho', bloco)

    def test_formato_vigente(self):
        bloco = montar_bloco_contexto([{
            'id': 2, 'referencia': 'CF/88 — art. 37',
            'texto': 'A Administração pública...', 'vigencia_de': '1988-10-05', 'vigencia_ate': None
        }])
        self.assertIn('vigente desde 1988-10-05', bloco)
        self.assertNotIn('VIGÊNCIA ENCERRADA', bloco)

    def test_empilha_trechos_numericados(self):
        trechos = [
            {'id': 1, 'referencia': 'Lei A', 'texto': 'texto um', 'vigencia_de': None, 'vigencia_ate': None},
            {'id': 2, 'referencia': 'Lei B', 'texto': 'texto dois', 'vigencia_de': None, 'vigencia_ate': None},
        ]
        bloco = montar_bloco_contexto(trechos)
        self.assertIn('[1] Lei A\ntexto um', bloco)
        self.assertIn('[2] Lei B\ntexto dois', bloco)


class TestMontarEvidencia(unittest.TestCase):

    def test_evidencia_com_ids_e_referencias(self):
        evidencia = montar_evidencia([
            {'id': 42, 'referencia': 'Lei nº 8.112/1990 — art. 117', 'texto': 'x'},
        ])
        self.assertEqual(evidencia, [{'id': 42, 'referencia': 'Lei nº 8.112/1990 — art. 117'}])

    def test_evidencia_vazia_sem_contexto(self):
        self.assertEqual(montar_evidencia([]), [])


class TestCortar(unittest.TestCase):

    def test_nao_corta_dentro_do_limite(self):
        self.assertEqual(legislacao._cortar('texto curto', 100), 'texto curto')

    def test_corta_em_borda_de_palavra(self):
        texto = 'palavra ' * 200  # 1600 chars
        cortado = legislacao._cortar(texto, 100)
        self.assertTrue(cortado.endswith('…'))
        self.assertNotIn('  ', cortado)
        self.assertLessEqual(len(cortado), 102)


if __name__ == '__main__':
    unittest.main()
