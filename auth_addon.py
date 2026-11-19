import os, json, time, hashlib, secrets
from flask import request, jsonify, session, redirect

AUTH_FILE = "auth_users.json"
LOG_FILE = "access_logs.json"

def _hash_pw(pw: str, salt: str = "") -> str:
    salt = salt or secrets.token_hex(8)
    return f"{salt}${hashlib.sha256(f'{salt}:{pw}'.encode()).hexdigest()}"

def _verify_pw(pw: str, stored: str) -> bool:
    if "$" not in stored: return False
    salt, h = stored.split("$", 1)
    return hashlib.sha256(f"{salt}:{pw}".encode()).hexdigest() == h

def _load(path, default):
    if not os.path.exists(path): return default
    try: return json.load(open(path, encoding="utf-8"))
    except Exception: return default

def _save(path, data):
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
def init_auth(app):
    app.secret_key = os.environ.get("ALHUJURAT_SECRET") or "alhujurat49by12-secret-key"
    if _load(AUTH_FILE, None) is None:
        _save(AUTH_FILE, {"admin": {"password_hash": _hash_pw(os.environ.get("ADMIN_PASS", "admin123")), "role": "admin", "active": True}, "users": {}})

    def log_act(actor, role, action, detail=""):
        logs = _load(LOG_FILE, [])
        logs.insert(0, {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "actor": actor or "unknown", "role": role or "guest", "ip": request.remote_addr or "127.0.0.1", "action": action, "detail": detail})
        _save(LOG_FILE, logs[:300])

    def cur_user():
        u, r = session.get("auth_user"), session.get("auth_role")
        if not u or not r: return None
        db = _load(AUTH_FILE, {"admin": {}, "users": {}})
        if r == "admin" and u == "admin" and db.get("admin", {}).get("active", True):
            return {"username": "admin", "role": "admin"}
        rec = db.get("users", {}).get(u)
        if r == "user" and rec and rec.get("active", False):
            return {"username": u, "role": "user"}
        return None
    @app.before_request
    def guard_req():
        path = request.path or "/"
        if path in ("/login", "/api/auth/login", "/api/auth/logout"): return None
        actor = cur_user()
        if not actor:
            log_act("anonymous", "blocked", "UNAUTHORIZED", f"{request.method} {path}")
            return (jsonify({"ok": False, "error": "লগইন প্রয়োজন।"}), 401) if path.startswith("/api/") else redirect("/login")
        if path.startswith("/api/admin/") and actor["role"] != "admin":
            log_act(actor["username"], actor["role"], "FORBIDDEN", f"{request.method} {path}")
            return jsonify({"ok": False, "error": "শুধুমাত্র অ্যাডমিন অনুমোদিত।"}), 403
        return None

    @app.route("/login", methods=["GET"])
    def login_page():
        return """<!doctype html><html lang="bn"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>Login</title><style>body{margin:0;padding:20px;font-family:Arial;background:#07110d;color:#e6f7ee;display:flex;justify-content:center;align-items:center;min-height:100vh}.card{width:100%;max-width:380px;background:#0d1f18;border:1px solid #1b4332;border-radius:12px;padding:18px}h2{margin:0 0 12px;color:#22c55e;text-align:center}input,button{width:100%;padding:10px;margin-top:8px;border-radius:8px;font-size:14px;box-sizing:border-box}input{background:#07120e;color:#ecfdf5;border:1px solid #234e3b}button{background:#16a34a;color:#fff;border:0;font-weight:700}.msg{margin-top:8px;color:#fca5a5;font-size:13px}</style></head><body><div class="card"><h2>ALHUJURAT49BY12</h2><input id="u" placeholder="username"/><input id="p" type="password" placeholder="password"/><button onclick="go()">Login</button><div class="msg" id="m"></div></div><script>async function go(){const r=await fetch("/api/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:u.value.trim(),password:p.value})});const j=await r.json();if(j.ok)location.href="/";else m.textContent=j.error||"Failed"}</script></body></html>"""
    @app.route("/api/auth/login", methods=["POST"])
    def api_login():
        b = request.get_json(silent=True) or {}
        u, p = str(b.get("username", "")).strip(), str(b.get("password", ""))
        db = _load(AUTH_FILE, {"admin": {}, "users": {}})
        adm = db.get("admin", {})
        if u == "admin" and adm.get("active", True) and _verify_pw(p, adm.get("password_hash", "")):
            session["auth_user"], session["auth_role"] = "admin", "admin"
            log_act("admin", "admin", "LOGIN_OK", "Admin login"); return jsonify({"ok": True, "role": "admin"})
        rec = db.get("users", {}).get(u)
        if rec and rec.get("active", False) and _verify_pw(p, rec.get("password_hash", "")):
            session["auth_user"], session["auth_role"] = u, "user"
            log_act(u, "user", "LOGIN_OK", "User login"); return jsonify({"ok": True, "role": "user"})
        log_act(u or "unknown", "denied", "LOGIN_FAIL", "Bad credentials"); return jsonify({"ok": False, "error": "ভুল ইউজারনেম বা পাসওয়ার্ড অথবা পারমিশন বন্ধ।"}), 401

    @app.route("/api/auth/logout", methods=["POST", "GET"])
    def api_logout():
        a = cur_user()
        if a: log_act(a["username"], a["role"], "LOGOUT", "")
        session.clear()
        return redirect("/login") if request.method == "GET" else jsonify({"ok": True})

    @app.route("/api/admin/users", methods=["GET"])
    def api_u_list():
        db = _load(AUTH_FILE, {"admin": {}, "users": {}})
        return jsonify({"ok": True, "users": {k: {"active": bool(v.get("active")), "created_at": v.get("created_at", "")} for k, v in db.get("users", {}).items()}})

    @app.route("/api/admin/users/create", methods=["POST"])
    def api_u_create():
        b = request.get_json(silent=True) or {}
        u, p, act = str(b.get("username", "")).strip(), str(b.get("password", "")), bool(b.get("active", True))
        if not u or len(p) < 4: return jsonify({"ok": False, "error": "ইউজার ও অন্তত ৪ অক্ষরের পাসওয়ার্ড দিন।"}), 400
        db = _load(AUTH_FILE, {"admin": {}, "users": {}})
        db.setdefault("users", {})[u] = {"password_hash": _hash_pw(p), "active": act, "created_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        _save(AUTH_FILE, db); log_act("admin", "admin", "CREATE_USER", f"{u} active={act}"); return jsonify({"ok": True})

    @app.route("/api/admin/users/toggle", methods=["POST"])
    def api_u_toggle():
        u = str((request.get_json(silent=True) or {}).get("username", "")).strip()
        db = _load(AUTH_FILE, {"admin": {}, "users": {}})
        if u not in db.get("users", {}): return jsonify({"ok": False, "error": "পাওয়া যায়নি"}), 404
        db["users"][u]["active"] = not bool(db["users"][u].get("active"))
        _save(AUTH_FILE, db); log_act("admin", "admin", "TOGGLE_USER", f"{u}={db['users'][u]['active']}"); return jsonify({"ok": True})

    @app.route("/api/admin/users/remove", methods=["POST"])
    def api_u_remove():
        u = str((request.get_json(silent=True) or {}).get("username", "")).strip()
        db = _load(AUTH_FILE, {"admin": {}, "users": {}})
        if u in db.get("users", {}): del db["users"][u]; _save(AUTH_FILE, db); log_act("admin", "admin", "REMOVE_USER", u)
        return jsonify({"ok": True})

    @app.route("/api/admin/password", methods=["POST"])
    def api_adm_pw():
        p = str((request.get_json(silent=True) or {}).get("new_password", ""))
        if len(p) < 4: return jsonify({"ok": False, "error": "অন্তত ৪ অক্ষর দিন।"}), 400
        db = _load(AUTH_FILE, {"admin": {}, "users": {}})
        db.setdefault("admin", {})["password_hash"] = _hash_pw(p); db["admin"]["active"] = True
        _save(AUTH_FILE, db); log_act("admin", "admin", "ADMIN_PW_CHANGED", ""); return jsonify({"ok": True})

    @app.route("/api/admin/logs", methods=["GET"])
    def api_adm_logs():
        return jsonify({"ok": True, "logs": _load(LOG_FILE, [])})
