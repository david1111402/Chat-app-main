from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, send
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
app.secret_key = "supersecret"  # required for sessions
socketio = SocketIO(app, async_mode="eventlet")

# ----------- Routes -----------

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        username = request.form.get("username")

        session["user"] = {
            "name": name,
            "email": email,
            "username": username
        }
        return redirect(url_for("chat"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        # In real apps, check password here!
        session["user"] = {"name": username, "username": username}
        return redirect(url_for("chat"))
    return render_template("log in page.html")

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("Link.html", user=session["user"])

# ----------- Socket.IO -----------

@socketio.on("message")
def handle_message(msg):
    print("Message:", msg)
    send(msg, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
