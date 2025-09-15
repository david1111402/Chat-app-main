import eventlet
eventlet.monkey_patch()  # ✅ must come before any other imports

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mysecret")

# Initialize SocketIO with eventlet
socketio = SocketIO(app, async_mode='eventlet')

# In-memory user store (replace with database in production)
users = {}

@app.route("/")
def index():
    if "username" in session:
        return render_template("chat.html", username=session["username"])
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["username"] = username
            return redirect(url_for("index"))
        else:
            return "Invalid username or password", 401
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            return "Username already exists", 400
        users[username] = password
        session["username"] = username
        return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

# --- SocketIO Events ---
@socketio.on("message")
def handle_message(msg):
    username = session.get("username", "Anonymous")
    send({"msg": msg, "user": username}, broadcast=True)

@socketio.on("join")
def handle_join(data):
    room = data["room"]
    join_room(room)
    send({"msg": f"{session['username']} has joined the room {room}."}, to=room)

@socketio.on("leave")
def handle_leave(data):
    room = data["room"]
    leave_room(room)
    send({"msg": f"{session['username']} has left the room {room}."}, to=room)

# --- Run for local dev ---
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
