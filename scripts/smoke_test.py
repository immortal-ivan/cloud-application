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
    return call("POST", "/auth/login", data={"username": username, "password": password})


def auth(token):
    return {"Authorization": "Bearer " + token}


code, body = call("GET", "/")
check("GET /", code == 200 and body["status"] == "running", body)
code, body = call("GET", "/status")
check("GET /status", code == 200 and body["status"] == "ok" and body["database"] == "ok", body)
check("GET /about", call("GET", "/about")[1]["framework"] == "FastAPI")
check("GET /course", call("GET", "/course")[1]["laboratory"] == 2)
check("Swagger UI /docs", call("GET", "/docs")[0] == 200)

check("логин с неверным паролем -> 401", login("student01", "wrong")[0] == 401)
tokens = {}
for user in ("student01", "student02", "student03"):
    code, tok = login(user, "Student#2026")
    check(f"POST /auth/login ({user})", code == 200 and tok["token_type"] == "bearer", tok)
    tokens[user] = tok["access_token"]
viewer, operator, administrator = (auth(tokens[u]) for u in ("student01", "student02", "student03"))

check("GET /services без токена -> 401", call("GET", "/services")[0] == 401)
check("неверный токен -> 401", call("GET", "/services", headers=auth("incorrect-token"))[0] == 401)
code, me = call("GET", "/auth/me", headers=viewer)
check("GET /auth/me (viewer)", code == 200 and me["role"] == "viewer" and "services.read" in me["permissions"], me)

code, services = call("GET", "/services", headers=viewer)
check("GET /services (viewer)", code == 200 and len(services) >= 3 and "type" in services[0], services)
check("POST /services (viewer) -> 403", call("POST", "/services", data={"name": "X1"}, headers=viewer)[0] == 403)
check("GET /access/roles (operator) -> 403", call("GET", "/access/roles", headers=operator)[0] == 403)
name = "Тест " + uuid.uuid4().hex[:6]
code, created = call("POST", "/services", data={"name": name, "type": "monitoring", "status": "running"}, headers=operator)
check("POST /services (operator) -> 201", code == 201 and created["type"] == "monitoring", created)
check("POST /services (неизвестный тип) -> 400", call("POST", "/services", data={"name": name + "x", "type": "nope"}, headers=operator)[0] == 400)
check("PUT /services/{id}", call("PUT", f"/services/{created['id']}", data={"name": name, "type": "monitoring", "status": "maintenance"}, headers=operator)[0] == 200)
code, filtered = call("GET", "/services?status=maintenance", headers=viewer)
check("GET /services?status=maintenance", code == 200 and any(x["id"] == created["id"] for x in filtered), filtered)
check("DELETE /services/{id}", call("DELETE", f"/services/{created['id']}", headers=operator)[0] == 200)
check("GET /services/{id} после удаления -> 404", call("GET", f"/services/{created['id']}", headers=viewer)[0] == 404)

boundary = uuid.uuid4().hex


def multipart(filename, data, ctype="text/plain"):
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    return body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}


payload, h = multipart("hello.txt", "Привет, облако".encode())
code, f = call("POST", "/files", raw=payload, headers={**viewer, **h})
check("POST /files (загрузка)", code == 201 and f["original_name"] == "hello.txt", f)
code, content = call("GET", f"/files/{f['id']}/download", headers=viewer)
check("GET /files/{id}/download", code == 200 and "Привет, облако".encode() in content, content)

payload, h = multipart("sample.txt", b"Cloud Application\nLaboratory work 18\n")
check("POST /objects (viewer) -> 403", call("POST", "/objects", raw=payload, headers={**viewer, **h})[0] == 403)
code, obj = call("POST", "/objects", raw=payload, headers={**operator, **h})
check("POST /objects (operator) -> 201", code == 201 and "storage_path" not in obj and obj["size_bytes"] == 37, obj)
code, content = call("GET", obj["download_url"], headers=viewer)
check("GET /objects/{id}/download (viewer)", code == 200 and b"Laboratory work 18" in content, content)
big, h = multipart("big.bin", b"0" * (5 * 1024 * 1024 + 1), "application/octet-stream")
check("файл больше 5 МБ -> 413", call("POST", "/objects", raw=big, headers={**operator, **h})[0] == 413)
check("DELETE /objects/{id} (operator)", call("DELETE", f"/objects/{obj['id']}", headers=operator)[0] == 200)
check("GET /objects/{id} после удаления -> 404", call("GET", f"/objects/{obj['id']}", headers=viewer)[0] == 404)

check("GET /users (viewer) -> 403", call("GET", "/users", headers=viewer)[0] == 403)
check("GET /access/roles (administrator)", call("GET", "/access/roles", headers=administrator)[0] == 200)
check("GET /access/summary (administrator)", call("GET", "/access/summary", headers=administrator)[0] == 200)
check("GET /access/summary (viewer) -> 403", call("GET", "/access/summary", headers=viewer)[0] == 403)

# смена роли действует без нового токена
code, user = call("GET", "/auth/me", headers=viewer)
check("viewer: POST /services -> 403", call("POST", "/services", data={"name": "Role Test"}, headers=viewer)[0] == 403)
call("PUT", f"/access/users/{user['id']}/role", data={"role": "operator"}, headers=administrator)
code, made = call("POST", "/services", data={"name": "Role Test " + uuid.uuid4().hex[:4]}, headers=viewer)
check("после смены роли на operator тот же токен -> 201", code == 201, made)
call("DELETE", f"/services/{made['id']}", headers=viewer)
call("PUT", f"/access/users/{user['id']}/role", data={"role": "viewer"}, headers=administrator)

check("POST /auth/logout", call("POST", "/auth/logout", headers=viewer)[0] == 204)
check("токен после logout недействителен", call("GET", "/auth/me", headers=viewer)[0] == 401)
code, tok = login("student02", "Student#2026")
check("DELETE /auth/session/{token}", call("DELETE", f"/auth/session/{tok['access_token']}")[0] == 200)
check("токен после удаления сеанса -> 401", call("GET", "/services", headers=auth(tok["access_token"]))[0] == 401)

print("FAILED:", failed)
sys.exit(1 if failed else 0)
