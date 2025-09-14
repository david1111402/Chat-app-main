from flask import Flask, render_template, request, redirect, jsonify, session
from flask_socketio import SocketIO, emit, join_room
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecret"
socketio = SocketIO(app, cors_allowed_origins="*")

DB_FILE = "chat.db"

# ---------- Database Helpers ----------
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    # users
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        admin_number TEXT,
        class TEXT,
        birthdate TEXT,
        username TEXT UNIQUE,
        allow_contact INTEGER
    )
    """)
    # messages
    conn.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room TEXT,
        user_id INTEGER,
        name TEXT,
        text TEXT,
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()

# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = request.form
        conn = get_db()
        conn.execute("""
            INSERT INTO users (name, email, admin_number, class, birthdate, username, allow_contact)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["name"], data["email"], data["admin_number"],
            data["class"], data["birthdate"], data["username"],
            1 if "allow_contact" in data else 0
        ))
        conn.commit()
        conn.close()
        return redirect("/login")
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()
        if user:
            session["user"] = dict(user)
            return redirect("/chat")
    return render_template("login.html")

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/login")
    return render_template("Link.html", user=session["user"])

@app.route("/call")
def call():
    if "user" not in session:
        return redirect("/login")
    return render_template("call.html")

@app.route("/history/<room>")
def history(room):
    conn = get_db()
    rows = conn.execute("SELECT * FROM messages WHERE room=? ORDER BY id ASC", (room,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/send", methods=["POST"])
def send():
    data = request.json
    conn = get_db()
    conn.execute("""
        INSERT INTO messages (room, user_id, name, text, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["room"], data["userId"], data["name"], data["text"], data["at"]
    ))
    conn.commit()
    conn.close()
    socketio.emit("message", data, room=data["room"])
    return "ok"

# ---------- Socket Events ----------
@socketio.on("join")
def on_join(data):
    room = data["room"]
    join_room(room)

if __name__ == "__main__":
    init_db()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
