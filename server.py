import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

socketio = SocketIO(app, async_mode="eventlet")

# Temporary in-memory "database"
users = {}

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")

        if not (name and username and password):
            return render_template("signup.html", error="All fields are required.")

        if username in users:
            return render_template("signup.html", error="Username already exists.")

        users[username] = {"name": name, "password": password}
        session["user"] = {"username": username, "name": name}
        return redirect(url_for("chat"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = users.get(username)
        if user and user["password"] == password:
            session["user"] = {"username": username, "name": user["name"]}
            return redirect(url_for("chat"))
        else:
            return render_template("login.html", error="Invalid username or password.")

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

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
