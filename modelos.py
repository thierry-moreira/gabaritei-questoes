# Arquivo: modelos.py
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, email, username, role, meta_diaria=0, tema='light'):
        self.id = id
        self.email = email
        self.username = username
        self.role = role
        self.meta_diaria = meta_diaria
        self.tema = tema
