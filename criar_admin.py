import sqlite3
from werkzeug.security import generate_password_hash

# Conectar ao banco de dados
conn = sqlite3.connect('condominio.db')
cursor = conn.cursor()

# Dados do administrador
email = 'admin@example.com'
senha = 'adminpassword123'  # Use uma senha forte em produção
senha_hash = generate_password_hash(senha)

# Inserir usuário administrador
try:
    cursor.execute('INSERT INTO usuarios (nome, email, senha_hash, tipo_usuario) VALUES (?, ?, ?, ?)',
                   ('Administrador', email, senha_hash, 'admin'))
    conn.commit()
    print(f"Administrador criado com sucesso. Use:\nEmail: {email}\nSenha: {senha}")
except sqlite3.IntegrityError:
    print("Erro: O email já está cadastrado.")
finally:
    conn.close()
