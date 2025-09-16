import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, send
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Initialize SocketIO with eventlet
socketio = SocketIO(app, async_mode="eventlet")

# In-memory user storage (replace with DB later if needed)
users = {}

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("chat"))
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not username or not email or not password:
            return "All fields are required!", 400

        if username in users:
            return "User already exists!", 400

        # Save user in memory
        users[username] = {"email": email, "password": password}

        print(f"New signup: {username} {email}")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = users.get(username)

        if user and user["password"] == password:
            session["user"] = {"name": username, "email": user["email"]}
            print(f"User logged in: {username}")
            return redirect(url_for("chat"))

        return "Invalid username or password", 401

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

# SocketIO events
@socketio.on("message")
def handle_message(msg):
    user = session.get("user", {}).get("name", "Anonymous")
    full_msg = f"{user}: {msg}"
    print(full_msg)
    send(full_msg, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
