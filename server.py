import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
import sqlite3
import os

app = Flask(__name__, static_folder="static")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

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
def home():
    return redirect(url_for("login"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Here you’d normally validate username/password
        return redirect(url_for("chat"))
    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Collect signup form data
        name = request.form.get("name")
        email = request.form.get("email")
        username = request.form.get("username")
        # For now, we just print — you could save to DB
        print("New signup:", name, email, username)
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route('/chat')
def chat():
    return render_template("Link.html")

@app.route('/history/<room>')
def history(room):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, room, user_id, name, text, timestamp FROM messages WHERE room=? ORDER BY id ASC",
        (room,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


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


if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=8080)
