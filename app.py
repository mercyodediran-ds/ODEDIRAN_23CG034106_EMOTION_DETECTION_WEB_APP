import os
import sqlite3
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from deepface import DeepFace
from datetime import datetime

# =====================================
# APP CONFIGURATION
# =====================================
app = Flask(__name__)
app.secret_key = "replace_with_a_secure_key"

# Folder for uploaded images
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Create uploads folder if missing
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
DB_PATH = "emotion_results.db"


# =====================================
# DATABASE SETUP
# =====================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            filename TEXT,
            emotion TEXT,
            scores TEXT,
            timestamp TEXT
        )"""
    )
    conn.commit()
    conn.close()


# =====================================
# FILE VALIDATION
# =====================================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# =====================================
# HOME / UPLOAD ROUTE
# =====================================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "Anonymous")
        file = request.files.get("image")

        # Validation
        if not file or file.filename == "":
            flash("⚠️ No file selected")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("❌ File type not allowed (use PNG, JPG, or JPEG)")
            return redirect(request.url)

        # Save file securely
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        try:
            print("✅ Starting DeepFace analysis...")
            obj = DeepFace.analyze(img_path=filepath, actions=["emotion"], enforce_detection=False)
            print("✅ DeepFace result:", obj)

            if isinstance(obj, list):
                obj = obj[0]

            dominant_emotion = obj.get("dominant_emotion", "unknown")
            scores = obj.get("emotion", {})

            print("Detected emotion:", dominant_emotion)
            print("Scores:", scores)

            # Save to DB
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO results (name, filename, emotion, scores, timestamp) VALUES (?, ?, ?, ?, ?)",
                (name, filename, dominant_emotion, str(scores), datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()

            # Render results page
            return render_template(
                "result.html",
                name=name,
                filename=filename,
                emotion=dominant_emotion,
                scores=scores,
                year=datetime.utcnow().year
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            flash(f"Error analyzing image: {e}")
            return redirect(request.url)

    return render_template("index.html", year=datetime.utcnow().year)


# =====================================
# HISTORY ROUTE
# =====================================
@app.route("/history")
def history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, filename, emotion, timestamp FROM results ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return render_template("history.html", rows=rows, year=datetime.utcnow().year)

# =====================================
# RUN APP
# =====================================
# Create database on every startup (Render doesn't persist files)
init_db()

if __name__ == "__main__":
    app.run(debug=True)
