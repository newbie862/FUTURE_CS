# app.py
import os
import base64
import json
from io import BytesIO
from flask import Flask, request, render_template, send_file, abort
from werkzeug.utils import secure_filename
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from dotenv import load_dotenv

# load .env
load_dotenv()
KEY_B64 = os.getenv("AES_KEY", "")
if not KEY_B64:
    raise SystemExit("ERROR: AES_KEY not set in .env")
KEY = base64.b64decode(KEY_B64)
if len(KEY) not in (16, 24, 32):
    raise SystemExit("ERROR: AES_KEY must be 16/24/32 bytes (base64)")

UPLOAD_DIR = "uploads_encrypted"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB cap

# --- Crypto helpers (AES-GCM) ---
def encrypt_bytes(plain: bytes):
    cipher = AES.new(KEY, AES.MODE_GCM)
    ct, tag = cipher.encrypt_and_digest(plain)
    return cipher.nonce, tag, ct

def decrypt_bytes(nonce: bytes, tag: bytes, ct: bytes):
    cipher = AES.new(KEY, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ct, tag)

# --- Routes ---
@app.route("/")
def index():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if not f:
        return "No file provided", 400
    orig_name = secure_filename(f.filename) or "unnamed"
    data = f.read()
    nonce, tag, ct = encrypt_bytes(data)
    fid = base64.urlsafe_b64encode(get_random_bytes(9)).decode().rstrip("=")
    bin_path = os.path.join(UPLOAD_DIR, f"{fid}.bin")
    meta_path = os.path.join(UPLOAD_DIR, f"{fid}.json")
    with open(bin_path, "wb") as b:
        b.write(ct)
    meta = {
        "orig_name": orig_name,
        "nonce": base64.b64encode(nonce).decode(),
        "tag": base64.b64encode(tag).decode()
    }
    with open(meta_path, "w") as m:
        json.dump(meta, m)
    return f"Uploaded as id: {fid}\n<a href='/files'>View files</a>"

@app.route("/files")
def files():
    entries = []
    for fn in os.listdir(UPLOAD_DIR):
        if fn.endswith(".json"):
            fid = fn[:-5]
            with open(os.path.join(UPLOAD_DIR, fn), "r") as j:
                meta = json.load(j)
            entries.append((fid, meta.get("orig_name", "unnamed")))
    return render_template("files.html", files=entries)

@app.route("/download/<fid>")
def download(fid):
    bin_path = os.path.join(UPLOAD_DIR, f"{fid}.bin")
    meta_path = os.path.join(UPLOAD_DIR, f"{fid}.json")
    if not os.path.exists(bin_path) or not os.path.exists(meta_path):
        abort(404)
    with open(meta_path, "r") as m:
        meta = json.load(m)
    ct = open(bin_path, "rb").read()
    try:
        nonce = base64.b64decode(meta["nonce"])
        tag = base64.b64decode(meta["tag"])
        plain = decrypt_bytes(nonce, tag, ct)
    except Exception as e:
        return "Decryption failed or file integrity check failed", 500
    return send_file(BytesIO(plain),
                     download_name=meta.get("orig_name", "file"),
                     as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
