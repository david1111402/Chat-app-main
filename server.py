import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecret")
socketio = SocketIO(app, async_mode="eventlet")

# -------------------- ROUTES --------------------

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        name = request.form.get("name")

        if not username or not name:
            return render_template("log in page (1).html", error="All fields are required")

        # Save user session
        session["user"] = {"username": username, "name": name}
        return redirect(url_for("chat"))

    return render_template("log in page (1).html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        name = request.form.get("name")

        if not username or not name:
            return render_template("log in page (1).html", error="All fields are required")

        # Save user session
        session["user"] = {"username": username, "name": name}
        return redirect(url_for("chat"))

    return render_template("log in page (1).html")

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("Link (1).html", user=session["user"])

# -------------------- SOCKET.IO --------------------
@socketio.on("message")
def handle_message(msg):
    print("Message:", msg)

# -------------------- MAIN --------------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
