import os
import sqlite3
import datetime
import mimetypes
from uuid import uuid4

from flask import Flask, request, jsonify, send_from_directory, Response
from openpyxl import Workbook, load_workbook

# ---------------- Paths ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = BASE_DIR  # your index.html, reporting.html, etc are here
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "reports.db")
EXCEL_PATH = os.path.join(BASE_DIR, "reports.xlsx")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------- App ----------------
app = Flask(__name__, static_folder=None)

# ---------------- DB helpers ----------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

with get_db() as conn:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            details TEXT,
            photo_path TEXT,
            created_at TEXT,
            ip TEXT
        )
        """
    )

# ---------------- Excel helpers ----------------
def append_to_excel(row: dict):
    """
    Append a row to reports.xlsx, creating it with headers if needed.
    Columns: created_at, name, email, details, photo_path, ip
    """
    headers = ["created_at", "name", "email", "details", "photo_path", "ip"]

    if not os.path.exists(EXCEL_PATH):
        wb = Workbook()
        ws = wb.active
        ws.title = "Reports"
        ws.append(headers)
        wb.save(EXCEL_PATH)

    try:
        wb = load_workbook(EXCEL_PATH)
        ws = wb.active
        # Ensure header row exists (in case file was replaced)
        if ws.max_row == 0:
            ws.append(headers)
        ws.append([row.get(h, "") for h in headers])
        wb.save(EXCEL_PATH)
    except Exception as e:
        # Don't block API on Excel error; log to console
        print("[append_to_excel] Error:", e)

# ---------------- Static / Frontend routes ----------------
def _send_html(name: str):
    path = os.path.join(FRONTEND_DIR, name)
    if not os.path.exists(path):
        return Response("Not found", status=404)
    return send_from_directory(FRONTEND_DIR, name)

@app.get("/")
def home():
    return _send_html("index.html")

@app.get("/reporting")
def reporting():
    return _send_html("reporting.html")

@app.get("/gdpr")
def gdpr():
    return _send_html("gdpr.html")

@app.get("/tobaccoinfo")
def tobaccoinfo():
    return _send_html("tobaccoinfo.html")

@app.get("/vapesinfo")
def vapesinfo():
    return _send_html("vapesinfo.html")

@app.get("/style.css")
def style_css():
    return send_from_directory(FRONTEND_DIR, "style.css")

@app.get("/script.js")
def script_js():
    return send_from_directory(FRONTEND_DIR, "script.js")

# ---------------- Uploads ----------------
@app.get("/uploads/<path:filename>")
def get_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# ---------------- Diagnostics (optional) ----------------
@app.get("/_where")
def where():
    return jsonify(
        base=BASE_DIR,
        frontend=FRONTEND_DIR,
        upload=UPLOAD_DIR,
        db=DB_PATH,
        excel=EXCEL_PATH,
    )

# ---------------- API: Submit Report ----------------
@app.post("/api/report")
def report():
    """
    Accepts either:
    - JSON: {name, email, details, photo_base64?}
    - multipart/form-data: fields name, email, details, and file 'photo'
    Saves to SQLite and appends to reports.xlsx.
    """
    content_type = request.headers.get("Content-Type", "")
    name = request.form.get("name") if "multipart/form-data" in content_type else (request.json or {}).get("name")
    email = request.form.get("email") if "multipart/form-data" in content_type else (request.json or {}).get("email")
    details = request.form.get("details") if "multipart/form-data" in content_type else (request.json or {}).get("details")

    # Basic validation (customize as needed)
    if not name or not email or not details:
        return jsonify(ok=False, error="Missing required fields: name, email, details"), 400

    # Handle optional photo (multipart upload)
    photo_path = None
    if "multipart/form-data" in content_type and "photo" in request.files:
        photo = request.files["photo"]
        if photo and photo.filename:
            ext = os.path.splitext(photo.filename)[1].lower()
            if not ext:
                # Try to guess from mimetype
                guessed = mimetypes.guess_extension(photo.mimetype or "")
                ext = guessed or ".bin"
            fname = f"{uuid4().hex}{ext}"
            dest = os.path.join(UPLOAD_DIR, fname)
            photo.save(dest)
            photo_path = f"/uploads/{fname}"

    # Meta
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    # Save to DB
    with get_db() as conn:
        conn.execute(
            "INSERT INTO reports(name,email,details,photo_path,created_at,ip) VALUES (?,?,?,?,?,?)",
            (name, email, details, photo_path, created_at, ip),
        )

    # Append to Excel
    append_to_excel({
        "created_at": created_at,
        "name": name,
        "email": email,
        "details": details,
        "photo_path": photo_path or "",
        "ip": ip or "",
    })

    return jsonify(ok=True, message="Report received. Thank you!")

# ---------------- Export spreadsheet ----------------
@app.get("/exports/reports.xlsx")
def download_excel():
    # Ensure file exists with headers so there's always something to download
    if not os.path.exists(EXCEL_PATH):
        append_to_excel({})
    return send_from_directory(BASE_DIR, "reports.xlsx", as_attachment=True)

# ---------------- Run ----------------
if __name__ == "__main__":
    # change host/port as needed
    app.run(host="127.0.0.1", port=5000, debug=False)
