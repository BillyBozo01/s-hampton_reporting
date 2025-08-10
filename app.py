import os, sqlite3, datetime, mimetypes
from uuid import uuid4
from flask import Flask, request, jsonify, send_from_directory

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = BASE_DIR  # HTML, CSS, and JS are in the same folder as app.py

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "reports.db")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, static_folder=None)

# --- DB ---
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

# Serve pages
@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.get("/tobacco.html")
def tobacco():
    return send_from_directory(FRONTEND_DIR, "tobacco.html")

@app.get("/vapes.html")
def vapes():
    return send_from_directory(FRONTEND_DIR, "vapes.html")

@app.get("/privacy.html")
def privacy():
    return send_from_directory(FRONTEND_DIR, "privacy.html")

# Serve static files
@app.get("/style.css")
def style():
    return send_from_directory(FRONTEND_DIR, "style.css")

@app.get("/script.js")
def script():
    return send_from_directory(FRONTEND_DIR, "script.js")



# --- Uploads (images only) ---
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

# --- API: receive report ---
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

  created_at = datetime.datetime.utcnow().isoformat()
  ip = request.headers.get("X-Forwarded-For", request.remote_addr)

  with get_db() as conn:
    conn.execute(
      "INSERT INTO reports(name,email,details,photo_path,created_at,ip) VALUES (?,?,?,?,?,?)",
      (name, email, details, photo_path, created_at, ip)
    )

  return jsonify(ok=True, message="Report received. Thank you!")

# --- Simple read-only admin (optional) ---
@app.get("/admin/reports")
def admin_list():
  token = request.args.get("token")
  expected = os.getenv("ADMIN_TOKEN")
  if not expected or token != expected:
    return "Forbidden", 403
  with get_db() as conn:
    rows = conn.execute(
      "SELECT id,name,email,details,photo_path,created_at,ip FROM reports ORDER BY id DESC"
    ).fetchall()
  lines = []
  for r in rows:
    lines.append(
      f"#{r['id']} | {r['created_at']} | name={r['name'] or '-'} | email={r['email'] or '-'} | ip={r['ip']}\n"
      f"details: {r['details']}\n"
      f"photo: {r['photo_path'] or '-'}\n"
      "----------------------------------------"
    )
  return ("\n".join(lines), 200, {"Content-Type": "text/plain; charset=utf-8"})

if __name__ == "__main__":
  app.run(host="127.0.0.1", port=5000, debug=True)
