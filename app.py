import os, sqlite3, datetime, mimetypes
from uuid import uuid4
from flask import Flask, request, jsonify, send_from_directory, Response

# ---------------- Paths (single-folder) ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = BASE_DIR            # HTML/CSS/JS next to app.py
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "reports.db")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------- App ----------------
app = Flask(__name__, static_folder=None)

# ---------------- Diagnostics (optional) ----------------
@app.get("/_where")
def _where():
    return Response(f"FRONTEND_DIR = {FRONTEND_DIR}", mimetype="text/plain")

@app.get("/_ls")
def _ls():
    try:
        files = sorted(os.listdir(FRONTEND_DIR))[:400]
        lines = [f"{'✓' if os.path.isfile(os.path.join(FRONTEND_DIR, f)) else '✗'}  {f}" for f in files]
        return Response("Listing FRONTEND_DIR:\n" + "\n".join(lines), mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return Response(f"Error listing dir: {e}", mimetype="text/plain; charset=utf-8")

print("Serving from:", FRONTEND_DIR)
for fn in ["reporting.html","tobaccoinfo.html","vapesinfo.html","gdpr.html","style.css","script.js"]:
    print(f" - {fn} exists:", os.path.exists(os.path.join(FRONTEND_DIR, fn)))

# ---------------- DB ----------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

with get_db() as conn:
    conn.execute("""
      CREATE TABLE IF NOT EXISTS reports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        details TEXT NOT NULL,
        photo_path TEXT,
        created_at TEXT NOT NULL,
        ip TEXT
      )
    """)

# ---------------- Frontend pages ----------------
@app.get("/")
def home():
    # Your home file is reporting.html
    return send_from_directory(FRONTEND_DIR, "reporting.html")

# Common assets
@app.get("/style.css")
def style():
    return send_from_directory(FRONTEND_DIR, "style.css")

@app.get("/script.js")
def script():
    return send_from_directory(FRONTEND_DIR, "script.js")

# Pretty URL mappings (optional; keep if your nav uses /tobacco.html etc.)
@app.get("/tobacco.html")
def tobacco_pretty():
    return send_from_directory(FRONTEND_DIR, "tobaccoinfo.html")

@app.get("/vapes.html")
def vapes_pretty():
    return send_from_directory(FRONTEND_DIR, "vapesinfo.html")

@app.get("/privacy.html")
def privacy_pretty():
    return send_from_directory(FRONTEND_DIR, "gdpr.html")

# Safe catch-all for other frontend files (serve .html/.css/.js directly)
@app.get("/<path:filename>")
def static_pages(filename):
    low = filename.lower()
    if not (low.endswith(".html") or low.endswith(".css") or low.endswith(".js")):
        return "Not found", 404
    path = os.path.join(FRONTEND_DIR, filename)
    print(f"[static_pages] {filename} -> {path} exists={os.path.isfile(path)}")
    if os.path.isfile(path):
        return send_from_directory(FRONTEND_DIR, filename)
    return Response(f"Not found: {filename}\nLooked in: {FRONTEND_DIR}", status=404, mimetype="text/plain")

# ---------------- Uploads (images only) ----------------
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}

def save_upload(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    guessed = (mimetypes.guess_type(file_storage.filename)[0] or "").lower()
    if guessed and guessed not in ALLOWED_MIME:
        return None
    ext = os.path.splitext(file_storage.filename)[1].lower()
    fname = f"{uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, fname)
    file_storage.save(path)
    return path

# ---------------- API ----------------
@app.post("/api/report")
def report():
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip()
    details = (request.form.get("details") or "").strip()

    if not details:
        return jsonify(ok=False, message="Details are required."), 400

    photo_path = None
    if "photo" in request.files and request.files["photo"].filename:
        photo_path = save_upload(request.files["photo"])
        if photo_path is None:
            return jsonify(ok=False, message="Unsupported file type."), 400

    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    with get_db() as conn:
        conn.execute(
            "INSERT INTO reports(name,email,details,photo_path,created_at,ip) VALUES (?,?,?,?,?,?)",
            (name, email, details, photo_path, created_at, ip)
        )

    return jsonify(ok=True, message="Report received. Thank you!")

# ---------------- Run ----------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
