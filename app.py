from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_session import Session
import sqlite3
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from functools import wraps
import firebase_admin
from firebase_admin import credentials, messaging

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Use uma chave secreta forte em produção

# Configuração para upload de arquivos
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Certifique-se de que o diretório de uploads existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configuração para sessões persistentes
app.config['SESSION_TYPE'] = 'filesystem'  # Armazena sessões no sistema de arquivos
Session(app)

# Configuração do Firebase Admin SDK com credenciais embutidas
firebase_cred = {
    "type": "service_account",
    "project_id": "appcondominio-2fcac",
    "private_key_id": "8c469fdb3033d16c59a7ce731b467542d2d6caa1",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQC980BYeZyhddRK\nGJjfbIxrMieAeqoZFptiYo0B9FWHjLdopcaXtwq1fAfCMprwrO2Nw7aLIanA0gt9\nI+wfNci7bkfI1X3yk2gkSKvZP36AWSPeCKFYiOxwoPxXWWacmo06sr9H9jKyrqjs\nIqBgZVkYPULAq+AW+cH2tHGhDtf9dM+kviqFXXSw3UY5p2/jpLDPDrH/tIUnFoMp\nfVFg9alZ0sHNW4Q/585ePg1ebdFHHfjIwEGWnDVQyUfezxUlJybb+aYlKqE1vEEE\nYRDQjA33ZrODwUstf8SCPycBxrvwyaYYL4gZXkYkj2pyG4cx1G+YEI1ryZvaUZ+8\n9jG7P4ILAgMBAAECggEAQL9/wgjmQsVa8Uz0I0ipjsrAW1O00qt5mO5V+YITe4qU\nZFgJ22JaBKX8MQ618O9JZIb/nOqDJkaTAvuxO6xGOdmsH4HilkL3/1JEPeAeW1rH\nVqKjeP3ndrbxfUbsqtol5QnUGRALlQvjaeadu24gkhojvHB6COrm2pUEnK1mI69M\n0RWQjn+NrKGCthzaUx4rJz7R9y3VGa5gLg6Mz4h+n89RTp/P/E91Bokyn/Dd4xns\ny9Rc4PGAhxNOumXd/OuiqqAfVTJczF3+Dss8tHtMrmxQj03v+E3aKGqAQxe7J0vm\nkZbGhExIdFSy+kqRQcTqdr9RA+IDESvvE3oohxeZoQKBgQDg2oWtspteM44C1NwH\nOjRIs1LH3XCipbg9iMC31lqcBSPOUiCwVo1lvOascS2/O0LbCFKupzu5FDa2SGpg\nqfi8s6jTIj/TrOMG+3wqX84e43UxHNVQU11kQdvpEF/PqCK1+ZBIjDff6R1mhVkP\nZivgX9QP6EPE9iJF77WOKVBHawKBgQDYQwc+kZYq0QrPxX648R/MGujFPWu7aTkq\n6qAFcAcM8AvqRjjvif5PdxfePCwO894YzFmOudVpsbgp9l8bu+FfDlJ8guIplhYx\nNSc18DY9ZTy/QDBK7a+vDMK84/dAuow0VpkPE6WgNGJxrDx9B1fnl/i+i1UIrNXg\nstRzFPp34QKBgQCcUg+BlJxDP2BJQ6a8N5DFwjWY0bBOwxt1XC9vH0zbDw+3jo0/\nSsz+n/dWh1CglBiEoiKpXYY9w3nN/EZIcaKFvflu3260QIuM/SVzaCuqecOtozgB\nohNZchfqzgFuIpwPGzNd3G2z8yMHdUlXVVbHpJePf5AtzFhDesUj0kEHhQKBgQCR\nQlR3XmqzT74nWMyJhMyK1/hJo7vdIgxYG0ho3pqdwg7+yTQtEU9UKPZLO7eMQ5mG\nppvxFjmWyNyesvGnO0diBci6AV/P9xPo8X7o5/RGwN1QyNinO4ep2LRlE+pb+/F4\npkIgsl2pggYtvDbU9D3DPXzC3+u56/2s8/Fna0vhgQKBgQC6V5wdAInAxxRCS9Fk\nH5FSeToReDVschP05vuqEUIgjrkZ75j4/C2utAi/y7myXGplY82VD9J672srgI6c\nZCWBxlrZytSe2jjC7W7GTywL7OZqFZ4nAYzAmbCuSxpRKD4WmhCKVOTfVc9gDN/h\nTrls7GHyzgdm0SIoj6fyy2mj6A==\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@appcondominio-2fcac.iam.gserviceaccount.com",
    "client_id": "117990932930345036538",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40appcondominio-2fcac.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}
cred = credentials.Certificate(firebase_cred)
firebase_admin.initialize_app(cred)

# Filtro personalizado para formatar datas
def datetime_to_local(value):
    if value:
        dt = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%Y-%m-%dT%H:%M')
    return value

app.jinja_env.filters['datetime_to_local'] = datetime_to_local
app.jinja_env.filters['strftime'] = lambda value, fmt: datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S').strftime(fmt) if value else value

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect('condominio.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Criação das tabelas (mantidas como no original)
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
        tipo_ocupacao TEXT,
        fcm_token TEXT  -- Adicionado para armazenar o token FCM
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
        FOREIGN KEY (remetente_id) REFERENCES usuarios (id),
        FOREIGN KEY (destinatario_id) REFERENCES usuarios (id)
    )
    ''')
    try:
        cursor.execute('ALTER TABLE mensagens ADD COLUMN status TEXT DEFAULT "Enviada"')
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    try:
        cursor.execute('ALTER TABLE mensagens ADD COLUMN data_lida TEXT')
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
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    )
    ''')
    try:
        cursor.execute('ALTER TABLE correspondencias ADD COLUMN status TEXT DEFAULT "Recebida"')
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
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    )
    ''')
    try:
        cursor.execute('ALTER TABLE anuncios ADD COLUMN titulo TEXT NOT NULL DEFAULT ""')
    except sqlite3.OperationalError:
        pass  # Coluna já existe
    try:
        cursor.execute('ALTER TABLE anuncios ADD COLUMN imagem TEXT')
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

    # Adicionar coluna fcm_token à tabela usuarios se não existir
    try:
        cursor.execute('ALTER TABLE usuarios ADD COLUMN fcm_token TEXT')
    except sqlite3.OperationalError:
        pass  # Coluna já existe

    conn.commit()
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

# Função para enviar notificação push com logs de depuração
def send_push_notification(token, title, body):
    if not token:
        print("Nenhum token FCM fornecido")
        return False
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=token,
    )
    try:
        response = messaging.send(message)
        print(f"Notificação enviada com sucesso para {token}: {response}")
        return True
    except Exception as e:
        print(f"Erro ao enviar notificação para {token}: {e}")
        return False

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
    conn.close()
    return render_template('index.html', usuario=usuario, avisos=avisos, mensagens=mensagens, moradores=moradores)

@app.route('/delete_mensagem/<int:mensagem_id>', methods=['POST'])
def delete_mensagem(mensagem_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE mensagens SET status = "Excluída", data_lida = ? WHERE id = ? AND destinatario_id = ?', 
                (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), mensagem_id, session['user_id']))
    if not cur.rowcount:
        conn.close()
        flash('Você não tem permissão para excluir esta mensagem!', 'error')
        return redirect(url_for('index'))
    conn.commit()
    conn.close()
    flash('Mensagem excluída com sucesso!', 'success')
    return redirect(url_for('index'))

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
            session.permanent = True  # Sessão persiste mesmo após fechar o app
            conn.close()
            return redirect(url_for('index'))
        conn.close()
        flash('Email ou senha incorretos!', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('tipo_usuario', None)
    return redirect(url_for('login'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['password']
        senha_hash = generate_password_hash(senha)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (nome, email, senha_hash, tipo_usuario) VALUES (?, ?, ?, ?)',
                         (nome, email, senha_hash, 'usuario'))
            conn.commit()
            flash('Cadastro realizado com sucesso!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email já cadastrado!', 'error')
        finally:
            conn.close()

    return render_template('cadastro.html')

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
            return redirect(url_for('admin'))
        except sqlite3.IntegrityError:
            flash('Email já cadastrado!', 'error')
        finally:
            conn.close()

    return render_template('cadastro_moradores.html')

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
    reservas_usuario = conn.execute('SELECT * FROM reservas WHERE usuario_id = ? ORDER BY data_inicio DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('reservas.html', todas_reservas=todas_reservas, reservas_usuario=reservas_usuario, tipo_usuario=usuario['tipo_usuario'])

@app.route('/editar_reserva/<int:reserva_id>', methods=['POST'])
def editar_reserva(reserva_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    reserva_atual = conn.execute('SELECT * FROM reservas WHERE id = ? AND usuario_id = ?', (reserva_id, session['user_id'])).fetchone()
    if not reserva_atual:
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
                   WHERE id = ? AND usuario_id = ?''', 
                   (area_comum, data_inicio_str, data_fim_str, reserva_id, session['user_id']))
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
    if not reserva:
        conn.close()
        flash('Você não tem permissão para cancelar esta reserva!', 'error')
        return redirect(url_for('reservas'))

    cur.execute('DELETE FROM reservas WHERE id = ? AND usuario_id = ?', (reserva_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Reserva cancelada com sucesso!', 'success')
    return redirect(url_for('reservas'))

@app.route('/pagamentos')
def pagamentos():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
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
        if 'titulo' in request.form:
            tipo_comunicacao = request.form['tipo_comunicacao']
            titulo = request.form['titulo']
            mensagem = request.form['mensagem']
            data_envio = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur = conn.cursor()

            if tipo_comunicacao == 'geral':
                cur.execute('''INSERT INTO avisos (titulo, mensagem, data_envio)
                                VALUES (?, ?, ?)''', (titulo, mensagem, data_envio))
                conn.commit()
                # Enviar notificação para todos os usuários
                for user in conn.execute('SELECT fcm_token FROM usuarios WHERE fcm_token IS NOT NULL').fetchall():
                    send_push_notification(user['fcm_token'], 'Novo Aviso', mensagem)
                flash('Aviso geral enviado com sucesso!', 'success')
            elif tipo_comunicacao == 'especifico':
                destinatario_id = request.form['destinatario_id']
                is_correspondencia = request.form.get('is_correspondencia', 'off') == 'on'
                tipo_correspondencia = request.form.get('tipo_correspondencia', None)
                cur.execute('''INSERT INTO mensagens (remetente_id, destinatario_id, titulo, mensagem, data_envio, status)
                                VALUES (?, ?, ?, ?, ?, ?)''', (session['user_id'], destinatario_id, titulo, mensagem, data_envio, 'Enviada'))
                if is_correspondencia and tipo_correspondencia:
                    cur.execute('''INSERT INTO correspondencias (usuario_id, tipo, descricao, data_recebimento, status)
                                    VALUES (?, ?, ?, ?, ?)''', (destinatario_id, tipo_correspondencia, mensagem, data_envio, 'Recebida'))
                conn.commit()
                # Enviar notificação ao destinatário
                token = conn.execute('SELECT fcm_token FROM usuarios WHERE id = ?', (destinatario_id,)).fetchone()['fcm_token']
                if token:
                    send_push_notification(token, 'Nova Mensagem', mensagem)
                flash('Mensagem enviada com sucesso!' + (' Correspondência registrada!' if is_correspondencia else ''), 'success')
        elif 'delete_mensagem_id' in request.form:
            mensagem_id = request.form['delete_mensagem_id']
            cur = conn.cursor()
            cur.execute('UPDATE mensagens SET status = "Excluída" WHERE id = ?', (mensagem_id,))
            conn.commit()
            flash('Mensagem excluída com sucesso!', 'success')
        elif 'edit_mensagem_id' in request.form:
            mensagem_id = request.form['edit_mensagem_id']
            titulo = request.form['titulo']
            mensagem = request.form['mensagem']
            data_envio = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur = conn.cursor()
            cur.execute('UPDATE mensagens SET titulo = ?, mensagem = ?, data_envio = ? WHERE id = ?',
                        (titulo, mensagem, data_envio, mensagem_id))
            conn.commit()
            flash('Mensagem editada com sucesso!', 'success')
        elif 'status' in request.form:
            correspondencia_id = request.form['correspondencia_id']
            status = request.form['status']
            cur = conn.cursor()
            correspondencia = conn.execute('SELECT usuario_id, tipo, data_recebimento FROM correspondencias WHERE id = ?', (correspondencia_id,)).fetchone()
            if status == 'Entregue' and correspondencia:
                mensagem_titulo = f"Chegada de Correspondência: {correspondencia['tipo']}"
                cur.execute('''UPDATE mensagens 
                               SET status = "Entregue", data_lida = ?
                               WHERE destinatario_id = ? AND titulo = ? AND data_envio = ? AND status != "Excluída"''', 
                            (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), correspondencia['usuario_id'], mensagem_titulo, correspondencia['data_recebimento']))
                cur.execute('UPDATE correspondencias SET status = ? WHERE id = ?', (status, correspondencia_id))
                conn.commit()
                flash('Correspondência marcada como entregue com sucesso!', 'success')

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
    titulo = request.form['titulo']
    mensagem = request.form['mensagem']
    data_envio = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute('''UPDATE avisos SET titulo = ?, mensagem = ?, data_envio = ? WHERE id = ?''',
                 (titulo, mensagem, data_envio, aviso_id))
    conn.commit()
    conn.close()
    flash('Aviso editado com sucesso!', 'success')
    return redirect(url_for('comunicacao'))

@app.route('/delete_aviso/<int:aviso_id>', methods=['POST'])
@admin_required
def delete_aviso(aviso_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM avisos WHERE id = ?', (aviso_id,))
    conn.commit()
    conn.close()
    flash('Aviso excluído com sucesso!', 'success')
    return redirect(url_for('comunicacao'))

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
        if 'tipo' in request.form and 'mensagem' in request.form:  # Envio de novo feedback
            tipo = request.form['tipo']
            mensagem = request.form['mensagem']
            data_envio = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur = conn.cursor()
            cur.execute('''INSERT INTO feedbacks (usuario_id, tipo, mensagem, data_envio)
                            VALUES (?, ?, ?, ?)''', (session['user_id'], tipo, mensagem, data_envio))
            conn.commit()
            flash('Feedback enviado com sucesso!', 'success')
        elif 'resposta_admin' in request.form:  # Resposta do administrador
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
        elif 'classificacao_usuario' in request.form:  # Classificação e resolução do usuário
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
        elif 'delete_feedback_id' in request.form:  # Exclusão do feedback pelo administrador
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

    if usuario['tipo_usuario'] == 'admin':
        correspondencias = conn.execute('SELECT c.*, u.nome AS usuario_nome FROM correspondencias c JOIN usuarios u ON c.usuario_id = u.id ORDER BY data_recebimento DESC').fetchall()
    else:
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

@app.route('/emergencias', methods=['GET', 'POST'])
@admin_required
def emergencias():
    if request.method == 'POST':
        conn = get_db_connection()
        titulo = request.form['titulo']
        procedimento = request.form['procedimento']
        contatos = request.form['contatos']

        cur = conn.cursor()
        cur.execute('''INSERT INTO emergencias (titulo, procedimento, contatos)
                        VALUES (?, ?, ?)''', (titulo, procedimento, contatos))
        conn.commit()
        conn.close()
        flash('Informação de emergência adicionada com sucesso!', 'success')
        return redirect(url_for('emergencias'))

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
        if 'tipo' in request.form and 'titulo' in request.form and 'descricao' in request.form:  # Criar novo anúncio
            tipo = request.form['tipo']
            titulo = request.form['titulo']
            descricao = request.form['descricao']
            data_criacao = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            imagem = None

            # Verifica se há um arquivo na requisição
            if 'imagem' in request.files:
                file = request.files['imagem']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    imagem = filename

            cur = conn.cursor()
            cur.execute('''INSERT INTO anuncios (usuario_id, tipo, titulo, descricao, data_criacao, imagem)
                            VALUES (?, ?, ?, ?, ?, ?)''', (session['user_id'], tipo, titulo, descricao, data_criacao, imagem))
            conn.commit()
            flash('Anúncio criado com sucesso!', 'success')
        elif 'delete_anuncio_id' in request.form:  # Excluir anúncio
            anuncio_id = request.form['delete_anuncio_id']
            anuncio = conn.execute('SELECT usuario_id, imagem FROM anuncios WHERE id = ?', (anuncio_id,)).fetchone()
            if anuncio['usuario_id'] != session['user_id']:
                flash('Você não tem permissão para excluir este anúncio!', 'error')
            else:
                # Remove a imagem do servidor, se existir
                if anuncio['imagem']:
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], anuncio['imagem']))
                    except OSError:
                        pass  # Ignora se o arquivo não existir
                cur = conn.cursor()
                cur.execute('DELETE FROM anuncios WHERE id = ? AND usuario_id = ?', (anuncio_id, session['user_id'],))
                conn.commit()
                flash('Anúncio excluído com sucesso!', 'success')

    anuncios = conn.execute('SELECT a.*, u.nome AS usuario_nome FROM anuncios a JOIN usuarios u ON a.usuario_id = u.id ORDER BY data_criacao DESC').fetchall()
    conn.close()
    return render_template('anuncios.html', anuncios=anuncios, usuario=usuario)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/forum', methods=['GET', 'POST'])
def forum():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    usuario = conn.execute('SELECT tipo_usuario FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        if 'titulo' in request.form and 'mensagem' in request.form:  # Criar nova postagem
            categoria = request.form['categoria']
            titulo = request.form['titulo']
            mensagem = request.form['mensagem']
            data_postagem = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur = conn.cursor()
            cur.execute('''INSERT INTO forum_posts (usuario_id, categoria, titulo, mensagem, data_postagem)
                            VALUES (?, ?, ?, ?, ?)''', (session['user_id'], categoria, titulo, mensagem, data_postagem))
            conn.commit()
            flash('Postagem criada com sucesso!', 'success')
        elif 'resposta_mensagem' in request.form:  # Criar resposta
            post_id = request.form['post_id']
            mensagem = request.form['resposta_mensagem']
            data_resposta = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur = conn.cursor()
            cur.execute('''INSERT INTO forum_respostas (post_id, usuario_id, mensagem, data_resposta)
                            VALUES (?, ?, ?, ?)''', (post_id, session['user_id'], mensagem, data_resposta))
            conn.commit()
            flash('Resposta enviada com sucesso!', 'success')
        elif 'delete_post_id' in request.form:  # Excluir postagem
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

@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')

@app.route('/register_token', methods=['POST'])
def register_token():
    if 'user_id' not in session:
        return 'Unauthorized', 401
    token = request.json.get('token')
    print(f"Token FCM recebido do frontend: {token}")  # Log para depuração
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE usuarios SET fcm_token = ? WHERE id = ?', (token, session['user_id']))
    conn.commit()
    conn.close()
    return 'Token registrado', 200

@app.route('/send_notification', methods=['POST'])
def send_notification():
    if 'user_id' not in session:
        return 'Unauthorized', 401
    conn = get_db_connection()
    user = conn.execute('SELECT fcm_token FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    token = user['fcm_token']
    if not token:
        print("Nenhum token FCM encontrado para o usuário")
        return 'Token não encontrado', 400
    
    title = request.form.get('title', 'Nova Notificação')
    body = request.form.get('body', 'Você tem uma nova mensagem no sistema!')
    print(f"Enviando notificação - Título: {title}, Corpo: {body}, Token: {token}")  # Log para depuração
    success = send_push_notification(token, title, body)
    if success:
        return f'Notificação enviada', 200
    return 'Erro ao enviar notificação', 500

if __name__ == '__main__':
    print("Iniciando o aplicativo Flask...")
    app.run(debug=True)
