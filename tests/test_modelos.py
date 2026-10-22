import os
import sys
import unittest

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modelos import User

class TestUserModel(unittest.TestCase):
    def test_inicializacao_usuario_padrao(self):
        """
        Garante que um usuário com valores padrão seja criado corretamente.
        """
        user = User(
            id="user123",
            email="estudante@email.com",
            username="Estudante Padrão",
            role="aluno"
        )
        
        self.assertEqual(user.id, "user123")
        self.assertEqual(user.email, "estudante@email.com")
        self.assertEqual(user.username, "Estudante Padrão")
        self.assertEqual(user.role, "aluno")
        self.assertEqual(user.meta_diaria, 0)
        self.assertEqual(user.tema, "light")

    def test_inicializacao_usuario_customizado(self):
        """
        Garante que um usuário customizado inicialize todos os atributos corretamente.
        """
        user = User(
            id="admin999",
            email="admin@gabaritei.com",
            username="Diretor Admin",
            role="admin",
            meta_diaria=20,
            tema="dark"
        )
        
        self.assertEqual(user.id, "admin999")
        self.assertEqual(user.email, "admin@gabaritei.com")
        self.assertEqual(user.username, "Diretor Admin")
        self.assertEqual(user.role, "admin")
        self.assertEqual(user.meta_diaria, 20)
        self.assertEqual(user.tema, "dark")

    def test_metodos_usermixin(self):
        """
        Verifica se os métodos herdados do UserMixin se comportam conforme o esperado.
        """
        user = User(
            id="user_mix_456",
            email="mix@email.com",
            username="Mixin Test",
            role="aluno"
        )
        
        # Por padrão, UserMixin define esses métodos/propriedades:
        self.assertTrue(user.is_authenticated)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_anonymous)
        self.assertEqual(user.get_id(), "user_mix_456")

if __name__ == '__main__':
    unittest.main()
