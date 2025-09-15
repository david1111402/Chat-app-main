import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room
import sqlite3
import os

app = Flask(__name__, static_folder=".", template_folder="templates")
app.secret_key = "supersecret"  # required for sessions
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
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            admin_number TEXT NOT NULL,
            class TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# ---------- Routes ----------
@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()

        if user:
            session["user"] = dict(user)
            return redirect(url_for("chat"))
        else:
            return render_template("log in page.html", error="Invalid username or password")

    return render_template("log in page.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        admin_number = request.form["admin_number"]
        class_name = request.form["class"]
        birth_date = request.form["birth_date"]
        username = request.form["username"]
        password = request.form["password"]

        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO users (name, email, admin_number, class, birth_date, username, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, email, admin_number, class_name, birth_date, username, password),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Username already taken")

    return render_template("register.html")

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("Link.html", user=session["user"])

@app.route("/styles.css")
def styles():
    return send_from_directory(".", "styles.css")

@app.route("/history/<room>")
def history(room):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, room, user_id, name, text, timestamp FROM messages WHERE room=? ORDER BY id ASC",
        (room,),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ---------- Socket Events ----------
@socketio.on("join")
def on_join(data):
    room = data["room"]
    join_room(room)

@socketio.on("message")
def handle_message(data):
    room = data["room"]
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO messages (room, user_id, name, text, timestamp) VALUES (?, ?, ?, ?, ?)",
        (room, data["userId"], data["name"], data["text"], data["at"]),
    )
    conn.commit()
    conn.close()
    emit("message", data, room=room)

# ---------- Init ----------
if __name__ == "__main__":
    init_db()
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
