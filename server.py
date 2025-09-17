aimport os
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecret")

socketio = SocketIO(app, async_mode="eventlet")

# In-memory store (replace with DB later if needed)
USERS = {}
MESSAGES = []

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("chat"))
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]

        if username in USERS:
            return "Username already exists!"

        USERS[username] = {
            "id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "username": username,
            "password": password
        }

        session["user"] = USERS[username]
        print(f"New signup: {name} {email} {username}")
        return redirect(url_for("chat"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = USERS.get(username)
        if not user or user["password"] != password:
            return "Invalid credentials!"

        session["user"] = user
        return redirect(url_for("chat"))

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

# SocketIO message handling
@socketio.on("send_message")
def handle_message(data):
    user = session.get("user")
    if not user:
        return

    msg = {
        "user": user["username"],
        "text": data["text"]
    }
    MESSAGES.append(msg)
    emit("new_message", msg, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
