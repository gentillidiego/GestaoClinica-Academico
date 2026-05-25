from flask_login import UserMixin
from database import query
from constants import Role

class User(UserMixin):
    def __init__(self, id, username, role, full_name=None, matricula=None):
        self.id = id
        self.username = username
        self.role = role
        self.full_name = full_name
        self.matricula = matricula

    @staticmethod
    def get(user_id):
        user_data = query("SELECT * FROM users WHERE id = %s", (user_id,), one=True)
        if user_data:
            return User(
                id=user_data['id'], 
                username=user_data['username'], 
                role=user_data['role'],
                full_name=user_data['full_name'] if 'full_name' in user_data.keys() else None,
                matricula=user_data['matricula'] if 'matricula' in user_data.keys() else None
            )
        return None

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_professor(self):
        return self.role == Role.PROFESSOR

    @property
    def is_aluno(self):
        return self.role == Role.ALUNO

    @property
    def is_atendimento(self):
        return self.role == Role.ATENDIMENTO
