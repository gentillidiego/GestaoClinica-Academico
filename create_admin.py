import os
import sys

from werkzeug.security import generate_password_hash
from database import execute, query, init_db
from constants import Role

def create_default_user():
    init_db()
    username = os.getenv('ADMIN_USERNAME')
    password = os.getenv('ADMIN_PASSWORD')
    role = Role.ADMIN

    if not username or not password:
        print("Defina ADMIN_USERNAME e ADMIN_PASSWORD antes de criar o administrador.")
        sys.exit(1)
    
    # Verifica se o usuário já existe
    existing_user = query("SELECT id FROM users WHERE username = %s", (username,), one=True)
    
    if not existing_user:
        hashed_password = generate_password_hash(password)
        execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, hashed_password, role))
        print(f"Usuário '{username}' criado com sucesso!")
    else:
        print(f"Usuário '{username}' já existe.")

if __name__ == '__main__':
    create_default_user()
