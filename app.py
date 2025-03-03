from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Use uma chave secreta forte em produção

# Filtro personalizado para formatar datas
def datetime_to_local(value):
    if value:
        dt = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%Y-%m-%dT%H:%M')
    return value

app.jinja_env.filters['datetime_to_local'] = datetime_to_local
app.jinja_env.filters['strftime'] = lambda value, fmt: datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S').strftime(fmt) if value else value

def get_db_connection():
    conn = sqlite3.connect('condominio.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        tipo_usuario TEXT,
        rua TEXT,
        numero TEXT,
        garagem TEXT,
        tipo_ocupacao TEXT
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
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS avisos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        mensagem TEXT NOT NULL,
        data_envio TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mensagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        remetente_id INTEGER,
        destinatario_id INTEGER,
        titulo TEXT NOT NULL,
        mensagem TEXT NOT NULL,
        data_envio TEXT,
        status TEXT DEFAULT 'Enviada',
        data_lida TEXT,
        lida INTEGER DEFAULT 0,
        FOREIGN KEY (remetente_id) REFERENCES usuarios (id),
        FOREIGN KEY (destinatario_id) REFERENCES usuarios (id)
    )
    ''')
    try:
        cursor.execute('ALTER TABLE mensagens ADD COLUMN lida INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        tipo_servico TEXT,
        descricao TEXT,
        status TEXT,
        data_solicitacao TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedbacks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        tipo TEXT,
        mensagem TEXT,
        data_envio TIMESTAMP,
        resposta_admin TEXT,
        data_resposta TIMESTAMP,
        classificacao_usuario INTEGER,
        resolvido_usuario TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    )
    ''')
    try:
        cursor.execute('ALTER TABLE feedbacks ADD COLUMN resposta_admin TEXT')
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    try:
        cursor.execute('ALTER TABLE feedbacks ADD COLUMN data_resposta TIMESTAMP')
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    try:
        cursor.execute('ALTER TABLE feedbacks ADD COLUMN classificacao_usuario INTEGER')
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    try:
        cursor.execute('ALTER TABLE feedbacks ADD COLUMN resolvido_usuario TEXT')
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS correspondencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        tipo TEXT,
        descricao TEXT,
        data_recebimento TIMESTAMP,
        status TEXT DEFAULT 'Recebida',
        lida INTEGER DEFAULT 0,
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    )
    ''')
    try:
        cursor.execute('ALTER TABLE correspondencias ADD COLUMN lida INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS veiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        placa TEXT UNIQUE,
        modelo TEXT,
        vaga_estacionamento INTEGER,
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emergencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT,
        procedimento TEXT,
        contatos TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS anuncios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        tipo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        data_criacao TIMESTAMP,
        lida INTEGER DEFAULT 0,
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    )
    ''')
    try:
        cursor.execute('ALTER TABLE anuncios ADD COLUMN lida INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS forum_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        categoria TEXT NOT NULL,
        titulo TEXT NOT NULL,
        mensagem TEXT NOT NULL,
        data_postagem TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    )
    ''')
    try:
        cursor.execute('ALTER TABLE forum_posts ADD COLUMN categoria TEXT NOT NULL')
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS forum_respostas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        usuario_id INTEGER,
        mensagem TEXT NOT NULL,
        data_resposta TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES forum_posts (id),
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    )
    ''')
    conn.commit()  # Salva as alterações no esquema
    return conn

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        conn = get_db_connection()
        user = conn.execute('SELECT tipo_usuario FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        if user['tipo_usuario'] != 'admin':
            flash('Acesso restrito a administradores.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    usuario = conn.execute('SELECT nome, tipo_usuario FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
    avisos = conn.execute('SELECT * FROM avisos ORDER BY data_envio DESC').fetchall()
    mensagens = conn.execute('SELECT * FROM mensagens WHERE destinatario_id = ? AND status != "Excluída" ORDER BY data_envio DESC',
                            (session['user_id'],)).fetchall()
    moradores = conn.execute('SELECT * FROM usuarios WHERE tipo_usuario = "usuario"').fetchall()

    # Contar itens não lidos
    mensagens_nao_lidas = conn.execute('SELECT COUNT(*) FROM mensagens WHERE destinatario_id = ? AND status != "Excluída" AND lida = 0',
                                       (session['user_id'],)).fetchone()[0]
    anuncios_nao_lidos = conn.execute('SELECT COUNT(*) FROM anuncios WHERE lida = 0').fetchone()[0]
    correspondencias_nao_lidas = conn.execute('SELECT COUNT(*) FROM correspondencias WHERE usuario_id = ? AND status = "Recebida" AND lida = 0',
                                              (session['user_id'],)).fetchone()[0]

    # Verificação para evitar divisão por zero no template
    if not avisos:
        avisos_limitados = []
    else:
        avisos_limitados = avisos[:3]  # Limita a 3 avisos no backend

    conn.close()
    return render_template('index.html', usuario=usuario, avisos=avisos_limitados, mensagens=mensagens, moradores=moradores,
                           mensagens_nao_lidas=mensagens_nao_lidas, anuncios_nao_lidos=anuncios_nao_lidos,
                           correspondencias_nao_lidas=correspondencias_nao_lidas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db_connection()
        email = request.form['email']
        password = request.form['password']
        user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        if user and check_password_hash(user['senha_hash'], password):
            session['user_id'] = user['id']
            session['tipo_usuario'] = user['tipo_usuario']
            return redirect(url_for('index'))
        conn.close()
        flash('Email ou senha incorretos!', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('tipo_usuario', None)
    return redirect(url_for('login'))

@app.route('/cadastro_moradores', methods=['GET', 'POST'])
@admin_required
def cadastro_moradores():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['password']
        rua = request.form.get('rua', '')
        numero = request.form.get('numero', '')
        garagem = request.form.get('garagem', '')
        tipo_ocupacao = request.form.get('tipo_ocupacao', '')
        senha_hash = generate_password_hash(senha)

        conn = get_db_connection()
        try:
            conn.execute('''INSERT INTO usuarios (nome, email, senha_hash, tipo_usuario, rua, numero, garagem, tipo_ocupacao)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                         (nome, email, senha_hash, 'usuario', rua, numero, garagem, tipo_ocupacao))
            conn.commit()
            flash('Morador cadastrado com sucesso!', 'success')
            return redirect(url_for('moradores'))
        except sqlite3.IntegrityError:
            flash('Email já cadastrado!', 'error')
        finally:
            conn.close()

    return render_template('cadastro_moradores.html')

@app.route('/moradores')
def moradores():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    moradores = conn.execute('SELECT * FROM usuarios WHERE tipo_usuario = "usuario"').fetchall()
    conn.close()
    return render_template('moradores.html', moradores=moradores)

@app.route('/editar_morador/<int:morador_id>', methods=['POST'])
@admin_required
def editar_morador(morador_id):
    conn = get_db_connection()
    cur = conn.cursor()
    nome = request.form['nome']
    email = request.form['email']
    rua = request.form['rua']
    numero = request.form['numero']
    garagem = request.form['garagem']
    tipo_ocupacao = request.form['tipo_ocupacao']

    try:
        cur.execute('''UPDATE usuarios SET nome = ?, email = ?, rua = ?, numero = ?, garagem = ?, tipo_ocupacao = ?
                       WHERE id = ? AND tipo_usuario = "usuario"''',
                    (nome, email, rua, numero, garagem, tipo_ocupacao, morador_id))
        conn.commit()
        flash('Informações do morador atualizadas com sucesso!', 'success')
    except sqlite3.IntegrityError:
        flash('Email já cadastrado por outro usuário!', 'error')
    finally:
        conn.close()

    return redirect(url_for('moradores'))

@app.route('/excluir_morador/<int:morador_id>', methods=['POST'])
@admin_required
def excluir_morador(morador_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM usuarios WHERE id = ? AND tipo_usuario = "usuario"', (morador_id,))
    conn.commit()
    conn.close()
    flash('Morador excluído com sucesso!', 'success')
    return redirect(url_for('moradores'))

@app.route('/reservas', methods=['GET', 'POST'])
def reservas():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    usuario = conn.execute('SELECT tipo_usuario FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        usuario_id = session['user_id']
        area_comum = request.form['area_comum']
        data_inicio = request.form['data_inicio']
        data_fim = request.form['data_fim']

        data_inicio_dt = datetime.datetime.strptime(data_inicio, '%Y-%m-%dT%H:%M')
        data_fim_dt = datetime.datetime.strptime(data_fim, '%Y-%m-%dT%H:%M')
        data_inicio_str = data_inicio_dt.strftime('%Y-%m-%d %H:%M:%S')
        data_fim_str = data_fim_dt.strftime('%Y-%m-%d %H:%M:%S')

        cur = conn.cursor()
        cur.execute('''SELECT * FROM reservas 
                       WHERE area_comum = ? 
                       AND (
                           (data_inicio < ? AND data_fim > ?) OR 
                           (data_inicio < ? AND data_fim > ?) OR 
                           (data_inicio >= ? AND data_fim <= ?)
                       )''', 
                       (area_comum, data_fim_str, data_inicio_str, data_fim_str, data_inicio_str, data_inicio_str, data_fim_str))
        conflitos = cur.fetchall()

        if conflitos:
            conn.close()
            flash('Horário conflita com outra reserva existente!', 'error')
            return redirect(url_for('reservas'))

        cur.execute('''INSERT INTO reservas (usuario_id, area_comum, data_inicio, data_fim)
                       VALUES (?, ?, ?, ?)''', (usuario_id, area_comum, data_inicio_str, data_fim_str))
        conn.commit()
        flash('Reserva feita com sucesso!', 'success')

    todas_reservas = conn.execute('SELECT r.*, u.nome AS usuario_nome FROM reservas r JOIN usuarios u ON r.usuario_id = u.id ORDER BY data_inicio DESC').fetchall()
    conn.close()
    return render_template('reservas.html', todas_reservas=todas_reservas, tipo_usuario=usuario['tipo_usuario'])

@app.route('/editar_reserva/<int:reserva_id>', methods=['POST'])
def editar_reserva(reserva_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    reserva_atual = conn.execute('SELECT * FROM reservas WHERE id = ? AND usuario_id = ?', (reserva_id, session['user_id'])).fetchone()
    if not reserva_atual and session.get('tipo_usuario') != 'admin':
        conn.close()
        flash('Você não tem permissão para editar esta reserva!', 'error')
        return redirect(url_for('reservas'))

    area_comum = request.form['area_comum']
    data_inicio = request.form['data_inicio']
    data_fim = request.form['data_fim']

    data_inicio_dt = datetime.datetime.strptime(data_inicio, '%Y-%m-%dT%H:%M')
    data_fim_dt = datetime.datetime.strptime(data_fim, '%Y-%m-%dT%H:%M')
    data_inicio_str = data_inicio_dt.strftime('%Y-%m-%d %H:%M:%S')
    data_fim_str = data_fim_dt.strftime('%Y-%m-%d %H:%M:%S')

    cur.execute('''SELECT * FROM reservas 
                   WHERE area_comum = ? 
                   AND id != ?
                   AND (
                       (data_inicio < ? AND data_fim > ?) OR 
                       (data_inicio < ? AND data_fim > ?) OR 
                       (data_inicio >= ? AND data_fim <= ?)
                   )''', 
                   (area_comum, reserva_id, data_fim_str, data_inicio_str, data_fim_str, data_inicio_str, data_inicio_str, data_fim_str))
    conflitos = cur.fetchall()

    if conflitos:
        conn.close()
        flash('Horário conflita com outra reserva existente!', 'error')
        return redirect(url_for('reservas'))

    cur.execute('''UPDATE reservas SET area_comum = ?, data_inicio = ?, data_fim = ? 
                   WHERE id = ?''', 
                   (area_comum, data_inicio_str, data_fim_str, reserva_id))
    conn.commit()
    conn.close()
    flash('Reserva modificada com sucesso!', 'success')
    return redirect(url_for('reservas'))

@app.route('/cancelar_reserva/<int:reserva_id>', methods=['POST'])
def cancelar_reserva(reserva_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    reserva = conn.execute('SELECT * FROM reservas WHERE id = ? AND usuario_id = ?', (reserva_id, session['user_id'])).fetchone()
    if not reserva and session.get('tipo_usuario') != 'admin':
        conn.close()
        flash('Você não tem permissão para cancelar esta reserva!', 'error')
        return redirect(url_for('reservas'))

    cur.execute('DELETE FROM reservas WHERE id = ?', (reserva_id,))
    conn.commit()
    conn.close()
    flash('Reserva cancelada com sucesso!', 'success')
    return redirect(url_for('reservas'))

@app.route('/pagamentos', methods=['GET', 'POST'])
def pagamentos():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if request.method == 'POST':
        usuario_id = request.form['usuario_id']
        valor = float(request.form['valor'])
        data_pagamento = request.form['data_pagamento']
        cur = conn.cursor()
        cur.execute('''INSERT INTO pagamentos (usuario_id, valor, data_pagamento)
                       VALUES (?, ?, ?)''', (usuario_id, valor, data_pagamento))
        conn.commit()
        flash('Pagamento registrado com sucesso!', 'success')

    pagamentos = conn.execute('SELECT * FROM pagamentos WHERE usuario_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('pagamentos.html', pagamentos=pagamentos)

@app.route('/comunicacao', methods=['GET', 'POST'])
@admin_required
def comunicacao():
    conn = get_db_connection()
    usuarios = conn.execute('SELECT id, nome FROM usuarios WHERE tipo_usuario = "usuario"').fetchall()
    correspondencias = conn.execute('SELECT c.*, u.nome AS usuario_nome FROM correspondencias c JOIN usuarios u ON c.usuario_id = u.id ORDER BY data_recebimento DESC').fetchall()

    if request.method == 'POST':
        cur = conn.cursor()
        print("Form data received:", dict(request.form))  # Log para depuração
        # Verifica exclusão de mensagem
        if 'delete_mensagem_id' in request.form:
            mensagem_id = request.form['delete_mensagem_id']
            print(f"Tentando excluir mensagem ID: {mensagem_id}")  # Log adicional
            mensagem = conn.execute('SELECT id FROM mensagens WHERE id = ?', (mensagem_id,)).fetchone()
            if mensagem:
                cur.execute('UPDATE mensagens SET status = "Excluída", data_lida = ? WHERE id = ?',
                            (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), mensagem_id))
                if cur.rowcount > 0:
                    conn.commit()
                    flash('Mensagem excluída com sucesso!', 'success')
                    print(f"Mensagem ID {mensagem_id} excluída com sucesso")
                else:
                    conn.rollback()
                    flash('Erro ao excluir a mensagem: nenhuma linha afetada!', 'error')
                    print(f"Falha ao excluir mensagem ID {mensagem_id}: nenhuma linha afetada")
            else:
                flash('Mensagem não encontrada!', 'error')
                print(f"Mensagem ID {mensagem_id} não encontrada")
        # Verifica edição de mensagem
        elif 'edit_mensagem_id' in request.form:
            mensagem_id = request.form['edit_mensagem_id']
            título = request.form['titulo']
            mensagem = request.form['mensagem']
            data_envio = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"Tentando editar mensagem ID: {mensagem_id}")  # Log adicional
            mensagem_existente = conn.execute('SELECT id FROM mensagens WHERE id = ?', (mensagem_id,)).fetchone()
            if mensagem_existente:
                cur.execute('UPDATE mensagens SET titulo = ?, mensagem = ?, data_envio = ? WHERE id = ?',
                            (título, mensagem, data_envio, mensagem_id))
                if cur.rowcount > 0:
                    conn.commit()
                    flash('Mensagem editada com sucesso!', 'success')
                    print(f"Mensagem ID {mensagem_id} editada com sucesso")
                else:
                    conn.rollback()
                    flash('Erro ao editar a mensagem: nenhuma linha afetada!', 'error')
                    print(f"Falha ao editar mensagem ID {mensagem_id}: nenhuma linha afetada")
            else:
                flash('Mensagem não encontrada!', 'error')
                print(f"Mensagem ID {mensagem_id} não encontrada para edição")
        # Verifica atualização de status de correspondência
        elif 'status' in request.form:
            correspondencia_id = request.form['correspondencia_id']
            status = request.form['status']
            correspondencia = conn.execute('SELECT usuario_id, tipo, data_recebimento FROM correspondencias WHERE id = ?', (correspondencia_id,)).fetchone()
            if status == 'Entregue' and correspondencia:
                mensagem_titulo = f"Chegada de Correspondência: {correspondencia['tipo']}"
                cur.execute('''UPDATE mensagens 
                               SET status = "Entregue", data_lida = ?, lida = 1
                               WHERE destinatario_id = ? AND titulo = ? AND data_envio = ? AND status != "Excluída"''', 
                            (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), correspondencia['usuario_id'], mensagem_titulo, correspondencia['data_recebimento']))
                cur.execute('UPDATE correspondencias SET status = ?, lida = 1 WHERE id = ?', (status, correspondencia_id))
                conn.commit()
                flash('Correspondência marcada como entregue com sucesso!', 'success')
        # Novo comunicado
        elif 'titulo' in request.form:
            tipo_comunicacao = request.form['tipo_comunicacao']
            título = request.form['titulo']
            mensagem = request.form['mensagem']
            data_envio = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if tipo_comunicacao == 'geral':
                cur.execute('''INSERT INTO avisos (titulo, mensagem, data_envio)
                                VALUES (?, ?, ?)''', (título, mensagem, data_envio))
                conn.commit()
                flash('Aviso geral enviado com sucesso!', 'success')
            elif tipo_comunicacao == 'especifico':
                destinatario_id = request.form['destinatario_id']
                is_correspondencia = request.form.get('is_correspondencia', 'off') == 'on'
                tipo_correspondencia = request.form.get('tipo_correspondencia', None)
                cur.execute('''INSERT INTO mensagens (remetente_id, destinatario_id, titulo, mensagem, data_envio, status, lida)
                                VALUES (?, ?, ?, ?, ?, ?, 0)''', (session['user_id'], destinatario_id, título, mensagem, data_envio, 'Enviada'))
                if is_correspondencia and tipo_correspondencia:
                    cur.execute('''INSERT INTO correspondencias (usuario_id, tipo, descricao, data_recebimento, status, lida)
                                    VALUES (?, ?, ?, ?, ?, 0)''', (destinatario_id, tipo_correspondencia, mensagem, data_envio, 'Recebida'))
                conn.commit()
                flash('Mensagem enviada com sucesso!' + (' Correspondência registrada!' if is_correspondencia else ''), 'success')

        conn.close()
        return redirect(url_for('comunicacao'))

    avisos = conn.execute('SELECT * FROM avisos ORDER BY data_envio DESC').fetchall()
    mensagens_enviadas = conn.execute('SELECT m.*, u.nome AS destinatario_nome FROM mensagens m JOIN usuarios u ON m.destinatario_id = u.id WHERE m.status != "Excluída" ORDER BY data_envio DESC').fetchall()
    conn.close()
    return render_template('comunicacao.html', avisos=avisos, mensagens_enviadas=mensagens_enviadas, usuarios=usuarios, correspondencias=correspondencias)

@app.route('/edit_aviso/<int:aviso_id>', methods=['POST'])
@admin_required
def edit_aviso(aviso_id):
    conn = get_db_connection()
    título = request.form['titulo']
    mensagem = request.form['mensagem']
    data_envio = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute('''UPDATE avisos SET titulo = ?, mensagem = ?, data_envio = ? WHERE id = ?''',
                 (título, mensagem, data_envio, aviso_id))
    conn.commit()
    conn.close()
    flash('Aviso editado com sucesso!', 'success')
    return redirect(url_for('comunicacao'))

@app.route('/delete_aviso/<int:aviso_id>', methods=['POST'])
@admin_required
def delete_aviso(aviso_id):
    conn = get_db_connection()
    cur = conn.cursor()
    print(f"Tentando excluir aviso ID: {aviso_id}")  # Log para depuração
    aviso = conn.execute('SELECT id FROM avisos WHERE id = ?', (aviso_id,)).fetchone()
    if aviso:
        cur.execute('DELETE FROM avisos WHERE id = ?', (aviso_id,))
        if cur.rowcount > 0:
            conn.commit()
            flash('Aviso excluído com sucesso!', 'success')
            print(f"Aviso ID {aviso_id} excluído com sucesso")
        else:
            conn.rollback()
            flash('Erro ao excluir o aviso: nenhuma linha afetada!', 'error')
            print(f"Falha ao excluir aviso ID {aviso_id}: nenhuma linha afetada")
    else:
        flash('Aviso não encontrado!', 'error')
        print(f"Aviso ID {aviso_id} não encontrado")
    conn.close()
    return redirect(url_for('comunicacao'))

@app.route('/mensagens', methods=['GET', 'POST'])
def mensagens():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    usuario = conn.execute('SELECT tipo_usuario FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST' and 'delete_mensagem_id' in request.form:
        mensagem_id = request.form['delete_mensagem_id']
        mensagem = conn.execute('SELECT destinatario_id FROM mensagens WHERE id = ?', (mensagem_id,)).fetchone()
        if mensagem and (mensagem['destinatario_id'] == session['user_id'] or usuario['tipo_usuario'] == 'admin'):
            cur = conn.cursor()
            cur.execute('UPDATE mensagens SET status = "Excluída", data_lida = ? WHERE id = ?',
                        (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), mensagem_id))
            conn.commit()
            flash('Mensagem excluída com sucesso!', 'success')
        else:
            flash('Você não tem permissão para excluir esta mensagem!', 'error')
        conn.close()
        return redirect(url_for('mensagens'))

    # Marcar mensagens como lidas
    cur = conn.cursor()
    cur.execute('UPDATE mensagens SET lida = 1 WHERE destinatario_id = ? AND status != "Excluída" AND lida = 0',
                (session['user_id'],))
    conn.commit()

    mensagens = conn.execute('SELECT m.*, u.nome AS remetente_nome FROM mensagens m JOIN usuarios u ON m.remetente_id = u.id WHERE m.destinatario_id = ? AND m.status != "Excluída" ORDER BY data_envio DESC',
                             (session['user_id'],)).fetchall()
    conn.close()
    return render_template('mensagens.html', mensagens=mensagens, usuario=usuario)

@app.route('/delete_mensagem/<int:mensagem_id>', methods=['POST'])
def delete_mensagem(mensagem_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    mensagem = conn.execute('SELECT destinatario_id FROM mensagens WHERE id = ?', (mensagem_id,)).fetchone()
    if mensagem and mensagem['destinatario_id'] == session['user_id']:
        cur.execute('UPDATE mensagens SET status = "Excluída", data_lida = ? WHERE id = ? AND destinatario_id = ?', 
                    (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), mensagem_id, session['user_id']))
        if not cur.rowcount:
            conn.close()
            flash('Você não tem permissão para excluir esta mensagem!', 'error')
            return redirect(url_for('mensagens'))
        conn.commit()
        flash('Mensagem excluída com sucesso!', 'success')
    else:
        flash('Você não tem permissão para excluir esta mensagem!', 'error')
    conn.close()
    return redirect(url_for('mensagens'))

@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        cur = conn.cursor()
        if senha:
            senha_hash = generate_password_hash(senha)
            cur.execute('''UPDATE usuarios SET nome = ?, email = ?, senha_hash = ? WHERE id = ?''',
                        (nome, email, senha_hash, session['user_id']))
        else:
            cur.execute('''UPDATE usuarios SET nome = ?, email = ? WHERE id = ?''',
                        (nome, email, session['user_id']))
        conn.commit()
        conn.close()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('perfil'))

    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('perfil.html', usuario=usuario)

@app.route('/relatorios', methods=['GET', 'POST'])
@admin_required
def relatorios():
    if request.method == 'POST':
        tipo_relatorio = request.form['tipo_relatorio']
        data_inicio = request.form['data_inicio']
        data_fim = request.form['data_fim']

        conn = get_db_connection()
        if tipo_relatorio == 'reservas':
            relatorios = conn.execute('''SELECT * FROM reservas WHERE data_inicio BETWEEN ? AND ?''',
                                      (data_inicio, data_fim)).fetchall()
        elif tipo_relatorio == 'pagamentos':
            relatorios = conn.execute('''SELECT * FROM pagamentos WHERE data_pagamento BETWEEN ? AND ?''',
                                      (data_inicio, data_fim)).fetchall()
        conn.close()
        return render_template('relatorios.html', relatorios=relatorios)

    return render_template('relatorios.html')

@app.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        tema = request.form['tema']
        notificacoes = 'notificacoes' in request.form

        flash('Configurações salvas com sucesso!', 'success')
        return redirect(url_for('configuracoes'))

    return render_template('configuracoes.html')

@app.route('/manutencao', methods=['GET', 'POST'])
def manutencao():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    usuario = conn.execute('SELECT tipo_usuario FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        tipo_servico = request.form['tipo_servico']
        descricao = request.form['descricao']
        data_solicitacao = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur = conn.cursor()
        cur.execute('''INSERT INTO servicos (usuario_id, tipo_servico, descricao, status, data_solicitacao)
                        VALUES (?, ?, ?, ?, ?)''', (session['user_id'], tipo_servico, descricao, 'Pendente', data_solicitacao))
        conn.commit()
        flash('Solicitação de serviço enviada com sucesso!', 'success')

    if usuario['tipo_usuario'] == 'admin':
        servicos = conn.execute('SELECT * FROM servicos').fetchall()
    else:
        servicos = conn.execute('SELECT * FROM servicos WHERE usuario_id = ?', (session['user_id'],)).fetchall()

    conn.close()
    return render_template('manutencao.html', servicos=servicos)

@app.route('/atualizar_status_manutencao/<int:servico_id>', methods=['POST'])
@admin_required
def atualizar_status_manutencao(servico_id):
    conn = get_db_connection()
    status = request.form['status']
    conn.execute('UPDATE servicos SET status = ? WHERE id = ?', (status, servico_id))
    conn.commit()
    conn.close()
    flash('Status atualizado com sucesso!', 'success')
    return redirect(url_for('manutencao'))

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    usuario = conn.execute('SELECT tipo_usuario FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        if 'tipo' in request.form and 'mensagem' in request.form:
            tipo = request.form['tipo']
            mensagem = request.form['mensagem']
            data_envio = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur = conn.cursor()
            cur.execute('''INSERT INTO feedbacks (usuario_id, tipo, mensagem, data_envio)
                            VALUES (?, ?, ?, ?)''', (session['user_id'], tipo, mensagem, data_envio))
            conn.commit()
            flash('Feedback enviado com sucesso!', 'success')
        elif 'resposta_admin' in request.form:
            if usuario['tipo_usuario'] != 'admin':
                flash('Apenas administradores podem responder feedbacks!', 'error')
            else:
                feedback_id = request.form['feedback_id']
                resposta_admin = request.form['resposta_admin']
                data_resposta = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur = conn.cursor()
                cur.execute('''UPDATE feedbacks SET resposta_admin = ?, data_resposta = ?
                               WHERE id = ?''', (resposta_admin, data_resposta, feedback_id))
                conn.commit()
                flash('Resposta enviada com sucesso!', 'success')
        elif 'classificacao_usuario' in request.form:
            feedback_id = request.form['feedback_id']
            feedback = conn.execute('SELECT usuario_id FROM feedbacks WHERE id = ?', (feedback_id,)).fetchone()
            if feedback['usuario_id'] != session['user_id']:
                flash('Você não tem permissão para classificar este feedback!', 'error')
            else:
                classificacao_usuario = int(request.form['classificacao_usuario'])
                resolvido_usuario = request.form['resolvido_usuario']
                cur = conn.cursor()
                cur.execute('''UPDATE feedbacks SET classificacao_usuario = ?, resolvido_usuario = ?
                               WHERE id = ?''', (classificacao_usuario, resolvido_usuario, feedback_id))
                conn.commit()
                flash('Classificação registrada com sucesso!', 'success')
        elif 'delete_feedback_id' in request.form:
            if usuario['tipo_usuario'] != 'admin':
                flash('Apenas administradores podem excluir feedbacks!', 'error')
            else:
                feedback_id = request.form['delete_feedback_id']
                feedback = conn.execute('SELECT classificacao_usuario FROM feedbacks WHERE id = ?', (feedback_id,)).fetchone()
                if feedback['classificacao_usuario'] is None:
                    flash('O feedback só pode ser excluído após a classificação do usuário!', 'error')
                else:
                    cur = conn.cursor()
                    cur.execute('DELETE FROM feedbacks WHERE id = ?', (feedback_id,))
                    conn.commit()
                    flash('Feedback excluído com sucesso!', 'success')

    feedbacks = conn.execute('SELECT f.*, u.nome AS usuario_nome FROM feedbacks f JOIN usuarios u ON f.usuario_id = u.id ORDER BY data_envio DESC').fetchall()
    conn.close()
    return render_template('feedback.html', feedbacks=feedbacks, usuario=usuario)

@app.route('/correspondencias')
def correspondencias():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    usuario = conn.execute('SELECT tipo_usuario FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()

    # Marcar correspondências como lidas ao visualizar
    cur = conn.cursor()
    if usuario['tipo_usuario'] == 'admin':
        correspondencias = conn.execute('SELECT c.*, u.nome AS usuario_nome FROM correspondencias c JOIN usuarios u ON c.usuario_id = u.id ORDER BY data_recebimento DESC').fetchall()
    else:
        cur.execute('UPDATE correspondencias SET lida = 1 WHERE usuario_id = ? AND status = "Recebida" AND lida = 0',
                    (session['user_id'],))
        conn.commit()
        correspondencias = conn.execute('SELECT * FROM correspondencias WHERE usuario_id = ? ORDER BY data_recebimento DESC', (session['user_id'],)).fetchall()

    conn.close()
    return render_template('correspondencias.html', correspondencias=correspondencias)

@app.route('/estacionamento', methods=['GET', 'POST'])
@admin_required
def estacionamento():
    conn = get_db_connection()
    if request.method == 'POST':
        placa = request.form['placa']
        modelo = request.form['modelo']
        vaga_estacionamento = request.form['vaga_estacionamento']

        cur = conn.cursor()
        cur.execute('''INSERT INTO veiculos (usuario_id, placa, modelo, vaga_estacionamento)
                        VALUES (?, ?, ?, ?)''', (session['user_id'], placa, modelo, vaga_estacionamento))
        conn.commit()
        conn.close()
        flash('Veículo registrado com sucesso!', 'success')
        return redirect(url_for('estacionamento'))

    veiculos = conn.execute('SELECT * FROM veiculos').fetchall()
    conn.close()
    return render_template('estacionamento.html', veiculos=veiculos)

@app.route('/emergencias')
@admin_required
def emergencias():
    conn = get_db_connection()
    emergencias = conn.execute('SELECT * FROM emergencias').fetchall()
    conn.close()
    return render_template('emergencias.html', emergencias=emergencias)

@app.route('/anuncios', methods=['GET', 'POST'])
def anuncios():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    usuario = conn.execute('SELECT tipo_usuario FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        if 'tipo' in request.form and 'descricao' in request.form:
            tipo = request.form['tipo']
            descricao = request.form['descricao']
            data_criacao = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur = conn.cursor()
            cur.execute('''INSERT INTO anuncios (usuario_id, tipo, descricao, data_criacao, lida)
                            VALUES (?, ?, ?, ?, 0)''', (session['user_id'], tipo, descricao, data_criacao))
            conn.commit()
            flash('Anúncio criado com sucesso!', 'success')
        elif 'delete_anuncio_id' in request.form:
            anuncio_id = request.form['delete_anuncio_id']
            anuncio = conn.execute('SELECT usuario_id FROM anuncios WHERE id = ?', (anuncio_id,)).fetchone()
            if anuncio['usuario_id'] != session['user_id']:
                flash('Você não tem permissão para excluir este anúncio!', 'error')
            else:
                cur = conn.cursor()
                cur.execute('DELETE FROM anuncios WHERE id = ? AND usuario_id = ?', (anuncio_id, session['user_id'],))
                conn.commit()
                flash('Anúncio excluído com sucesso!', 'success')

    # Marcar anúncios como lidos ao visualizar
    cur = conn.cursor()
    cur.execute('UPDATE anuncios SET lida = 1 WHERE lida = 0')
    conn.commit()

    anuncios = conn.execute('SELECT a.*, u.nome AS usuario_nome FROM anuncios a JOIN usuarios u ON a.usuario_id = u.id ORDER BY data_criacao DESC').fetchall()
    conn.close()
    return render_template('anuncios.html', anuncios=anuncios, usuario=usuario)

@app.route('/forum', methods=['GET', 'POST'])
def forum():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    usuario = conn.execute('SELECT tipo_usuario FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        if 'titulo' in request.form and 'mensagem' in request.form:
            categoria = request.form['categoria']
            título = request.form['titulo']
            mensagem = request.form['mensagem']
            data_postagem = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur = conn.cursor()
            cur.execute('''INSERT INTO forum_posts (usuario_id, categoria, titulo, mensagem, data_postagem)
                            VALUES (?, ?, ?, ?, ?)''', (session['user_id'], categoria, título, mensagem, data_postagem))
            conn.commit()
            flash('Postagem criada com sucesso!', 'success')
        elif 'resposta_mensagem' in request.form:
            post_id = request.form['post_id']
            mensagem = request.form['resposta_mensagem']
            data_resposta = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur = conn.cursor()
            cur.execute('''INSERT INTO forum_respostas (post_id, usuario_id, mensagem, data_resposta)
                            VALUES (?, ?, ?, ?)''', (post_id, session['user_id'], mensagem, data_resposta))
            conn.commit()
            flash('Resposta enviada com sucesso!', 'success')
        elif 'delete_post_id' in request.form:
            post_id = request.form['delete_post_id']
            post = conn.execute('SELECT usuario_id FROM forum_posts WHERE id = ?', (post_id,)).fetchone()
            if post['usuario_id'] != session['user_id']:
                flash('Você não tem permissão para excluir esta postagem!', 'error')
            else:
                cur = conn.cursor()
                cur.execute('DELETE FROM forum_respostas WHERE post_id = ?', (post_id,))
                cur.execute('DELETE FROM forum_posts WHERE id = ? AND usuario_id = ?', (post_id, session['user_id'],))
                conn.commit()
                flash('Postagem excluída com sucesso!', 'success')

    categoria_filtro = request.args.get('categoria', '')
    if categoria_filtro:
        posts = conn.execute('SELECT p.*, u.nome AS usuario_nome FROM forum_posts p JOIN usuarios u ON p.usuario_id = u.id WHERE p.categoria = ? ORDER BY data_postagem DESC', (categoria_filtro,)).fetchall()
    else:
        posts = conn.execute('SELECT p.*, u.nome AS usuario_nome FROM forum_posts p JOIN usuarios u ON p.usuario_id = u.id ORDER BY data_postagem DESC').fetchall()

    posts_com_respostas = []
    for post in posts:
        respostas = conn.execute('SELECT r.*, u.nome AS usuario_nome FROM forum_respostas r JOIN usuarios u ON r.usuario_id = u.id WHERE r.post_id = ? ORDER BY data_resposta ASC', (post['id'],)).fetchall()
        posts_com_respostas.append((post, respostas))

    conn.close()
    return render_template('forum.html', posts_com_respostas=posts_com_respostas, usuario=usuario, categoria_filtro=categoria_filtro)

if __name__ == '__main__':
    app.run(debug=True)
