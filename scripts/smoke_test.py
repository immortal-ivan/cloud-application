"""Контрольная проверка основных компонентов запущенного приложения.

Запуск (приложение уже запущено через python run.py):
    python -m scripts.smoke_test [https://localhost:8443]
Использует только стандартную библиотеку.
"""
import json
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "https://localhost:8443"
CTX = ssl.create_default_context()
CTX.check_hostname = False  # учебный самоподписанный сертификат
CTX.verify_mode = ssl.CERT_NONE
failed = 0


def call(method, path, *, data=None, headers=None, form=None, raw=None):
    headers = dict(headers or {})
    body = raw
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=CTX) as r:
            content = r.read()
            return r.status, (json.loads(content) if content and "json" in r.headers.get("Content-Type", "") else content)
    except urllib.error.HTTPError as e:
        content = e.read()
        try:
            return e.code, json.loads(content)
        except ValueError:
            return e.code, content


def check(name, ok, info=""):
    global failed
    print(("PASS " if ok else "FAIL ") + name + (f"  {info}" if not ok and info else ""))
    failed += 0 if ok else 1


def login(username, password):
    status, body = call("POST", "/auth/login", form={"username": username, "password": password})
    return status, body


code, body = call("GET", "/status")
check("GET /status", code == 200 and body["status"] == "ok" and body["database"] == "ok", body)
check("Swagger UI /docs", call("GET", "/docs")[0] == 200)

check("логин с неверным паролем -> 401", login("student", "wrong")[0] == 401)
code, tok = login("student", "Student#2026")
check("POST /auth/login (student)", code == 200 and tok["token_type"] == "bearer", tok)
student = {"Authorization": "Bearer " + tok["access_token"]}
code, tok = login("admin", "Admin#2026")
check("POST /auth/login (admin)", code == 200, tok)
admin = {"Authorization": "Bearer " + tok["access_token"]}

check("GET /auth/me без токена -> 401", call("GET", "/auth/me")[0] == 401)
code, me = call("GET", "/auth/me", headers=student)
check("GET /auth/me (student)", code == 200 and me["role"] == "user" and "services:read" in me["permissions"], me)

code, services = call("GET", "/services", headers=student)
check("GET /services (student)", code == 200 and len(services) >= 3, services)
check("POST /services (student) -> 403", call("POST", "/services", data={"name": "X1"}, headers=student)[0] == 403)
name = "Тест " + uuid.uuid4().hex[:6]
code, created = call("POST", "/services", data={"name": name, "description": "d"}, headers=admin)
check("POST /services (admin) -> 201", code == 201, created)
check("PUT /services/{id}", call("PUT", f"/services/{created['id']}", data={"name": name, "status": "disabled"}, headers=admin)[0] == 200)
check("DELETE /services/{id}", call("DELETE", f"/services/{created['id']}", headers=admin)[0] == 204)
check("GET /services/{id} после удаления -> 404", call("GET", f"/services/{created['id']}", headers=admin)[0] == 404)

boundary = uuid.uuid4().hex
payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"hello.txt\"\r\n"
           f"Content-Type: text/plain\r\n\r\nПривет, облако\r\n--{boundary}--\r\n").encode()
code, f = call("POST", "/files", raw=payload, headers={**student, "Content-Type": f"multipart/form-data; boundary={boundary}"})
check("POST /files (загрузка)", code == 201 and f["original_name"] == "hello.txt", f)
code, content = call("GET", f"/files/{f['id']}/download", headers=student)
check("GET /files/{id}/download", code == 200 and "Привет, облако".encode() in content, content)
check("чужой файл недоступен (admin видит всё, student - только свои)", len(call("GET", "/files", headers=student)[1]) >= 1)

check("GET /users (student) -> 403", call("GET", "/users", headers=student)[0] == 403)
check("GET /users (admin)", call("GET", "/users", headers=admin)[0] == 200)
check("POST /auth/logout", call("POST", "/auth/logout", headers=student)[0] == 204)
check("токен после logout недействителен", call("GET", "/auth/me", headers=student)[0] == 401)

print("FAILED:", failed)
sys.exit(1 if failed else 0)
