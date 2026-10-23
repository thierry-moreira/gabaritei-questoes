import os
import sys
import unittest

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import slugify

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

if __name__ == '__main__':
    unittest.main()
