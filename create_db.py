import sqlite3

conn = sqlite3.connect('condominio.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    tipo_usuario TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS reservas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    area_comum TEXT,
    data_inicio TIMESTAMP,
    data_fim TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS pagamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    valor REAL,
    data_pagamento TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
)
''')

conn.commit()
conn.close()