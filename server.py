import eventlet
eventlet.monkey_patch()

from flask import Flask, send_from_directory, jsonify
from flask_socketio import SocketIO, emit, join_room
import sqlite3
import os

app = Flask(__name__, static_folder='.')
socketio = SocketIO(app, cors_allowed_origins="*")

DB_FILE = "messages.db"

# ---------- Database Helpers ----------
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# ---------- Routes ----------
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/Link.html')
def link():
    return send_from_directory('.', 'Link.html')

@app.route('/styles.css')
def styles():
    return send_from_directory('.', 'styles.css')

@app.route('/history/<room>')
def history(room):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, room, user_id, name, text, timestamp FROM messages WHERE room=? ORDER BY id ASC",
        (room,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ---------- Socket Events ----------
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO messages (room, user_id, name, text, timestamp) VALUES (?, ?, ?, ?, ?)",
        (room, data['userId'], data['name'], data['text'], data['at'])
    )
    conn.commit()
    conn.close()
    emit('message', data, room=room)

# ---------- Entry Point ----------
if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

