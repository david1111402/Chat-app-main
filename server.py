import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room
import os

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey123")

socketio = SocketIO(app, async_mode="eventlet")

# In-memory user store (for example)
users = {}

@app.route("/")
def landing():
    if "user" in session:
        return redirect(url_for("chat"))
    return render_template("landing.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        # simple checks
        if not (name and email and username and password):
            return render_template("signup.html", error="Please fill all fields")
        if username in users:
            return render_template("signup.html", error="Username already taken")
        users[username] = {"name": name, "email": email, "password": password}
        session["user"] = {"name": name, "username": username}
        return redirect(url_for("chat"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not (username and password):
            return render_template("login.html", error="Please provide credentials")
        user = users.get(username)
        if user and user["password"] == password:
            session["user"] = {"name": user["name"], "username": username}
            return redirect(url_for("chat"))
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("Link.html", user=session["user"])

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# socket.io events, etc.
@socketio.on("message")
def handle_message(data):
    user = session.get("user", {}).get("name", "Anonymous")
    data_to_emit = {
        "userId": data.get("userId"),
        "name": user,
        "text": data.get("text"),
        "at": data.get("at"),
        "room": data.get("room")
    }
    emit("message", data_to_emit, broadcast=True)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
