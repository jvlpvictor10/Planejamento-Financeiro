from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__, static_folder='.')
app.config['SECRET_KEY'] = 'chave_secreta_finapp_2026'
DB_NAME = 'database.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    with open('schema.sql', 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

# Servir a página inicial do App
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Rota de Registro
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    name = data.get('name')
    username = (data.get('username') or '').strip().lower()
    password = data.get('password')
    initial_balance = float(data.get('initial_balance', 0.0))

    if not name or not username or not password:
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Nome de usuário já cadastrado'}), 409

    pwd_hash = generate_password_hash(password)
    cursor.execute('INSERT INTO users (name, username, password_hash) VALUES (?, ?, ?)',
                   (name, username, pwd_hash))
    user_id = cursor.lastrowid

    cursor.execute('INSERT INTO user_settings (user_id, initial_balance) VALUES (?, ?)',
                   (user_id, initial_balance))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Cadastrado com sucesso', 'user': {'id': user_id, 'name': name, 'username': username}}), 201

# Rota de Login
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip().lower()
    password = data.get('password')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, username, password_hash FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Usuário ou senha inválidos'}), 401

    return jsonify({
        'message': 'Login com sucesso',
        'user': {'id': user['id'], 'name': user['name'], 'username': user['username']}
    })

if __name__ == '__main__':
    if not os.path.exists(DB_NAME):
        init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
