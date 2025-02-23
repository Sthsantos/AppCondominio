import sqlite3
from werkzeug.security import generate_password_hash

# Conectar ao banco de dados
conn = sqlite3.connect('condominio.db')
cursor = conn.cursor()

# Inserir usuário de teste
email = 'test@example.com'
senha = 'password123'  # Nunca use senhas fracas em produção
senha_hash = generate_password_hash(senha)

cursor.execute('INSERT INTO usuarios (nome, email, senha_hash, tipo_usuario) VALUES (?, ?, ?, ?)',
               ('Teste Usuario', email, senha_hash, 'morador'))

conn.commit()
conn.close()

print(f"Usuário criado com sucesso. Use:\nEmail: {email}\nSenha: {senha}")