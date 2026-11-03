import os
import sys
import unittest

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import (
    slugify,
    validar_username,
    validar_texto_comentario,
    USERNAME_MAX,
    TEXTO_COMENTARIO_MAX,
)

class TestUtils(unittest.TestCase):
    
    # -------------------------------------------------------------------------
    # Testes para a função slugify
    # -------------------------------------------------------------------------
    def test_slugify_com_texto_simples(self):
        """Garante que strings normais em minúsculas e maiúsculas sejam convertidas corretamente."""
        self.assertEqual(slugify("Direito Administrativo"), "direito-administrativo")
        self.assertEqual(slugify("Lei 8112"), "lei-8112")
        
    def test_slugify_com_acentos_e_caracteres_especiais(self):
        """Garante a remoção adequada de acentos e substituição de caracteres especiais."""
        self.assertEqual(slugify("Ação de Inconstitucionalidade!"), "acao-de-inconstitucionalidade")
        self.assertEqual(slugify("Língua Portuguesa & Redação"), "lingua-portuguesa-redacao")
        self.assertEqual(slugify("Órgãos Públicos - União"), "orgaos-publicos-uniao")
        
    def test_slugify_com_espacos_e_hifens_extras(self):
        """Garante que hifens múltiplos ou espaços nas pontas sejam tratados devidamente."""
        self.assertEqual(slugify("  espaços   no   meio  "), "espacos-no-meio")
        self.assertEqual(slugify("---texto-com-hifens---"), "texto-com-hifens")
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify(None), "")

    # -------------------------------------------------------------------------
    # F-11 — validação de username (fonte do nome exibido nos comentários)
    # -------------------------------------------------------------------------
    def test_validar_username_aceita_e_normaliza(self):
        self.assertEqual(
            validar_username("  Aluno   Teste  "), ("Aluno Teste", "")
        )
        self.assertEqual(validar_username("concurseiro_01"), ("concurseiro_01", ""))
        self.assertEqual(validar_username("João-Henrique.Silva"), ("João-Henrique.Silva", ""))

    def test_validar_username_rejeita_html_e_tamanho(self):
        self.assertIsNone(validar_username("<img src=x onerror=alert(1)>")[0])
        self.assertIsNone(validar_username("Aluno<script>")[0])
        self.assertIsNone(validar_username("a")[0])
        self.assertIsNone(validar_username("a" * (USERNAME_MAX + 1))[0])
        self.assertIsNone(validar_username(None)[0])

    # -------------------------------------------------------------------------
    # F-11 — validação do texto do comentário
    # -------------------------------------------------------------------------
    def test_validar_texto_comentario_aceita_texto_legitimo(self):
        self.assertEqual(
            validar_texto_comentario("  Comentário útil.  "),
            ("Comentário útil.", ""),
        )
        # < e > são permitidos no armazenamento; a saída é que codifica.
        self.assertEqual(
            validar_texto_comentario("Se x < 5 e y > 2, então..."),
            ("Se x < 5 e y > 2, então...", ""),
        )

    def test_validar_texto_comentario_rejeita_invalidos(self):
        self.assertIsNone(validar_texto_comentario("")[0])
        self.assertIsNone(validar_texto_comentario("   ")[0])
        self.assertIsNone(validar_texto_comentario(None)[0])
        self.assertIsNone(
            validar_texto_comentario("x" * (TEXTO_COMENTARIO_MAX + 1))[0]
        )
        self.assertIsNone(validar_texto_comentario("texto\x01controle")[0])

if __name__ == '__main__':
    unittest.main()
