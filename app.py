import os
import json
import base64
import hashlib
import socket
import urllib.request
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "fortress_data.json")

MASTER_ADMIN = "Md Borat Ullah (এমডি বরাতুল্লাহ)"
MASTER_PASS = "Mssharmin@2222@AGI"

TRACKER_DOMAINS = {
    "doubleclick.net",
    "googlesyndication.com",
    "google-analytics.com",
    "facebook.com/tr",
    "adservice.google.com",
    "scorecardresearch.com",
}


def hash_password(password: str, salt: str = "ALHUJURAT49BY12_SALT") -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return dk.hex()


MASTER_PASS_HASH = hash_password(MASTER_PASS)


def derive_key(secret: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, 100000, dklen=32)


def encrypt_vault_text(plain_text: str, secret: str) -> dict:
    salt = os.urandom(16)
    key = derive_key(secret, salt)
    data_bytes = plain_text.encode("utf-8")
    keystream = hashlib.sha256(key + salt).digest()
    stream = bytearray()
    while len(stream) < len(data_bytes):
        keystream = hashlib.sha256(keystream + key).digest()
        stream.extend(keystream)
    cipher_bytes = bytes(b ^ stream[i] for i, b in enumerate(data_bytes))
    mac = hashlib.sha256(key + cipher_bytes).hexdigest()
    return {
        "salt": base64.b64encode(salt).decode("ascii"),
        "cipher": base64.b64encode(cipher_bytes).decode("ascii"),
        "mac": mac,
    }


def decrypt_vault_text(payload: dict, secret: str) -> str:
    if not payload or "cipher" not in payload or "salt" not in payload or "mac" not in payload:
        return ""
    salt = base64.b64decode(payload["salt"].encode("ascii"))
    cipher_bytes = base64.b64decode(payload["cipher"].encode("ascii"))
    key = derive_key(secret, salt)
    expected_mac = hashlib.sha256(key + cipher_bytes).hexdigest()
    if expected_mac != payload["mac"]:
        raise ValueError("Vault integrity check failed")
    keystream = hashlib.sha256(key + salt).digest()
    stream = bytearray()
    while len(stream) < len(cipher_bytes):
        keystream = hashlib.sha256(keystream + key).digest()
        stream.extend(keystream)
    plain_bytes = bytes(b ^ stream[i] for i, b in enumerate(cipher_bytes))
    return plain_bytes.decode("utf-8")
def default_state() -> dict:
    return {
        "users": {f"User {i}": True for i in range(6)},
        "vault_encrypted": None,
        "privacy_filter_enabled": True,
    }


def load_state() -> dict:
    if not os.path.exists(DATA_FILE):
        state = default_state()
        save_state(state)
        return state
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        base = default_state()
        base.update(data)
        if "users" not in data or not isinstance(data["users"], dict):
            base["users"] = default_state()["users"]
        return base
    except Exception:
        return default_state()


def save_state(state: dict) -> None:
    tmp_file = DATA_FILE + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp_file, DATA_FILE)


def check_tor_control_signal() -> tuple[bool, str]:
    try:
        with socket.create_connection(("127.0.0.1", 9051), timeout=2) as sock:
            sock.sendall(b'AUTHENTICATE ""\r\nSIGNAL NEWNYM\r\nQUIT\r\n')
            resp = sock.recv(1024).decode("utf-8", errors="ignore")
            if "250" in resp:
                return True, "Tor NEWNYM circuit rotation sent"
            return False, f"Tor control response: {resp.strip()}"
    except Exception:
        return False, "Tor control port (9051) not reachable"


def fetch_real_ip() -> tuple[str, str]:
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass
    try:
        req = urllib.request.Request("https://api.ipify.org", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as r:
            public_ip = r.read().decode("utf-8").strip()
            return public_ip, f"Live Public IP (Local: {local_ip})"
    except Exception:
        return local_ip, "Offline / No external IP lookup (Local interface)"


@app.after_request
def add_privacy_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ALHUJURAT49BY12 — Privacy Fortress</title>
<style>
  body { background:#070b08; color:#d8ffe2; font-family:monospace; margin:0; padding:16px; }
  .box { max-width:520px; margin:auto; border:1px solid #1f8a4c; border-radius:10px; padding:16px; background:#0d1610; }
  h2 { color:#4ade80; margin-top:0; text-align:center; }
  .info { background:#102216; border:1px dashed #22c55e; padding:10px; border-radius:8px; margin-bottom:14px; font-size:13px; }
  .row { display:flex; justify-content:space-between; align-items:center; background:#122017; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1d3b27; }
  button { cursor:pointer; border:none; border-radius:6px; padding:8px 12px; font-family:monospace; font-weight:bold; }
  .on { background:#16a34a; color:#fff; }
  .off { background:#dc2626; color:#fff; }
  .primary { background:#22c55e; color:#061109; width:100%; padding:11px; margin-top:8px; }
  .danger { background:#b91c1c; color:#fff; width:100%; padding:11px; margin-top:8px; }
  textarea, input { width:100%; box-sizing:border-box; background:#08100b; color:#e2ffe9; border:1px solid #256d3e; border-radius:8px; padding:10px; font-family:monospace; margin-top:6px; }
  .muted { color:#86efac; font-size:12px; margin-top:6px; }
  #appPanel { display:none; }
</style>
</head>
<body>
<div class="box">
  <h2>ALHUJURAT49BY12</h2>
  <div class="info">
    <div>Admin: {{ admin }}</div>
    <div id="ipStatus">IP Status: Checking...</div>
    <div id="torStatus" class="muted">Tor Control: Checking...</div>
  </div>
  <div id="lockPanel">
    <label>Master Password:</label>
    <input type="password" id="passInput" placeholder="Enter master password">
    <button class="primary" onclick="unlockApp()">Unlock Fortress</button>
    <div id="loginMsg" class="muted"></div>
  </div>
  <div id="appPanel">
    <div class="row">
      <div><div><strong>Tor Circuit Rotate (NEWNYM)</strong></div><div class="muted" id="torDetail">127.0.0.1:9051 signal</div></div>
      <button class="on" onclick="rotateTor()">Rotate</button>
    </div>
    <div class="row">
      <div><div><strong>Anti-Tracker Domain Guard</strong></div><div class="muted" id="trackerDetail">Tracker domain check</div></div>
      <button id="filterBtn" class="on" onclick="toggleFilter()">ON</button>
    </div>
    <input type="text" id="urlCheckInput" placeholder="Test URL or domain">
    <button class="primary" onclick="checkUrlPrivacy()">Check Domain Privacy</button>
    <div id="urlCheckResult" class="muted"></div>
    <h3>Users Access Control</h3>
    <div id="usersList"></div>
    <h3>Encrypted Vault</h3>
    <textarea id="vaultBox" rows="5" placeholder="Write private notes..."></textarea>
    <button class="primary" onclick="saveVault()">Encrypt & Save</button>
    <button class="danger" onclick="lockApp()">Lock</button>
    <div id="vaultMsg" class="muted"></div>
  </div>
</div>
<script>
let currentPassword = "", filterEnabled = true;
async function refreshIp() {
  const d = await (await fetch("/api/status")).json();
  ipStatus.innerText = "IP Status: " + d.ip + " (" + d.ip_note + ")";
  torStatus.innerText = "Tor Control: " + d.tor_detail;
  filterEnabled = d.privacy_filter_enabled;
  filterBtn.innerText = filterEnabled ? "ON" : "OFF";
  filterBtn.className = filterEnabled ? "on" : "off";
}
async function unlockApp() {
  const pw = passInput.value;
  const d = await (await fetch("/api/verify",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({password:pw})})).json();
  if (!d.ok) { loginMsg.innerText = "Invalid password."; return; }
  currentPassword = pw; passInput.value = ""; loginMsg.innerText = "";
  lockPanel.style.display = "none"; appPanel.style.display = "block";
  await loadUsers(); await loadVault(); await refreshIp();
}
function lockApp() {
  currentPassword = ""; vaultBox.value = "";
  appPanel.style.display = "none"; lockPanel.style.display = "block";
}
async function loadUsers() {
  const d = await (await fetch("/api/users")).json();
  usersList.innerHTML = "";
  Object.entries(d.users).forEach(([n, a]) => {
    const r = document.createElement("div"); r.className = "row";
    const s = document.createElement("span"); s.innerText = n;
    const b = document.createElement("button"); b.className = a ? "on" : "off"; b.innerText = a ? "ON" : "OFF";
    b.onclick = () => toggleUser(n); r.append(s, b); usersList.append(r);
  });
}
async function toggleUser(n) {
  await fetch("/api/toggle_user",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({user:n,password:currentPassword})});
  await loadUsers();
}
async function loadVault() {
  const d = await (await fetch("/api/load",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({password:currentPassword})})).json();
  if (d.ok) { vaultBox.value = d.text || ""; vaultMsg.innerText = d.message || ""; }
}
async function saveVault() {
  const d = await (await fetch("/api/save",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:vaultBox.value,password:currentPassword})})).json();
  vaultMsg.innerText = d.message || "Saved.";
}
async function rotateTor() {
  const d = await (await fetch("/api/tor/rotate",{method:"POST"})).json();
  torDetail.innerText = d.message; await refreshIp();
}
async function toggleFilter() {
  const d = await (await fetch("/api/filter/toggle",{method:"POST"})).json();
  filterEnabled = d.privacy_filter_enabled;
  filterBtn.innerText = filterEnabled ? "ON" : "OFF"; filterBtn.className = filterEnabled ? "on" : "off";
}
async function checkUrlPrivacy() {
  const d = await (await fetch("/api/privacy/check",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({target:urlCheckInput.value})})).json();
  urlCheckResult.innerText = d.message;
}
refreshIp();
</script>
</body>
</html>
"""
def is_authorized(password: str) -> bool:
    return bool(password) and hash_password(password) == MASTER_PASS_HASH


@app.route("/")
def index():
    return render_template_string(HTML_PAGE, admin=MASTER_ADMIN)


@app.route("/api/status")
def api_status():
    state = load_state()
    ip, note = fetch_real_ip()
    ok, detail = check_tor_control_signal()
    return jsonify({
        "ip": ip,
        "ip_note": note,
        "tor_reachable": ok,
        "tor_detail": detail,
        "privacy_filter_enabled": bool(state.get("privacy_filter_enabled", True)),
    })


@app.route("/api/verify", methods=["POST"])
def api_verify():
    body = request.get_json(silent=True) or {}
    pw = body.get("password", "")
    return jsonify({"ok": is_authorized(pw)})


@app.route("/api/users")
def api_users():
    state = load_state()
    return jsonify({"users": state["users"]})


@app.route("/api/toggle_user", methods=["POST"])
def api_toggle_user():
    body = request.get_json(silent=True) or {}
    if not is_authorized(body.get("password", "")):
        return jsonify({"ok": False, "message": "Unauthorized"}), 401
    user_name = body.get("user", "")
    state = load_state()
    if user_name in state["users"]:
        state["users"][user_name] = not bool(state["users"][user_name])
        save_state(state)
    return jsonify({"ok": True, "users": state["users"]})


@app.route("/api/save", methods=["POST"])
def api_save():
    body = request.get_json(silent=True) or {}
    pw = body.get("password", "")
    if not is_authorized(pw):
        return jsonify({"ok": False, "message": "Unauthorized"}), 401
    text = body.get("text", "")
    state = load_state()
    state["vault_encrypted"] = encrypt_vault_text(text, pw)
    save_state(state)
    return jsonify({"ok": True, "message": "Encrypted with PBKDF2 + XOR/HMAC and saved to fortress_data.json."})


@app.route("/api/load", methods=["POST"])
def api_load():
    body = request.get_json(silent=True) or {}
    pw = body.get("password", "")
    if not is_authorized(pw):
        return jsonify({"ok": False, "message": "Unauthorized"}), 401
    state = load_state()
    enc = state.get("vault_encrypted")
    if not enc:
        return jsonify({"ok": True, "text": "", "message": "Vault is currently empty."})
    try:
        text = decrypt_vault_text(enc, pw)
        return jsonify({"ok": True, "text": text, "message": "Decrypted & loaded from fortress_data.json."})
    except Exception as e:
        return jsonify({"ok": False, "text": "", "message": f"Decrypt error: {e}"})


@app.route("/api/tor/rotate", methods=["POST"])
def api_tor_rotate():
    ok, detail = check_tor_control_signal()
    return jsonify({"ok": ok, "message": detail})


@app.route("/api/filter/toggle", methods=["POST"])
def api_filter_toggle():
    state = load_state()
    state["privacy_filter_enabled"] = not bool(state.get("privacy_filter_enabled", True))
    save_state(state)
    return jsonify({"ok": True, "privacy_filter_enabled": state["privacy_filter_enabled"]})


@app.route("/api/privacy/check", methods=["POST"])
def api_privacy_check():
    state = load_state()
    body = request.get_json(silent=True) or {}
    target = (body.get("target") or "").strip().lower()
    if not state.get("privacy_filter_enabled", True):
        return jsonify({"ok": True, "message": "Anti-Tracker Domain Guard is OFF."})
    if not target:
        return jsonify({"ok": False, "message": "Enter a URL or domain to test."})
    matched = [d for d in TRACKER_DOMAINS if d in target]
    if matched:
        return jsonify({"ok": True, "message": f"Flagged tracker match: {', '.join(matched)} (Block/avoid in browser)."})
    return jsonify({"ok": True, "message": f"No known tracker domain matched in '{target}'."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
