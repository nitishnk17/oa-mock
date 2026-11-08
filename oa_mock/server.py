"""HTTP server: serves the web app and runs code. Listens on 127.0.0.1 only.

GET  /                               home page: your companies, and ones you can download
GET  /api/library                    companies here and on GitHub, git status, the running job
POST /api/library                    {action: check|download|update|remove, company} -> starts a job (see library.py)
GET  /api/library/job                progress of the running job
GET  /<company>                      the test app for one company
GET  /static/...                     CSS, JS and vendored libraries from web/static/
GET  /api/companies                  JSON list of companies
GET  /api/companies/<company>/data.js   window.OA_DATA = {config, questions} without hidden tests
GET  /api/companies/<company>/questions/<id>/tests   hidden tests (for questions graded in the browser)
POST /api/grade                      {company, qid, lang, code, scope} -> per-test results (C++, Java, Python)
POST /run                            {lang, code, inputs[], limit} -> {results[]} or {compile_error}
GET  /api/submissions?company=&qid=  past submissions, newest first (see submissions.py)
GET  /api/submissions/<company>/<qid>/<id>    one submission with its code
POST /api/submissions                save a submission
DELETE /api/submissions/<company>/<qid>/<id>

/run, /api/grade, /api/library and /api/submissions need the X-Token header the pages carry.
"""
import html, json, mimetypes, os, secrets
from urllib.parse import parse_qs, urlsplit
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import data, grading, judge, library, submissions

WEB_DIR = os.path.join(data.ROOT, "web")
STATIC_DIR = os.path.join(WEB_DIR, "static")
TOKEN = secrets.token_hex(16)   # /run only accepts requests from pages this server rendered
MAX_INPUTS = 50

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")


def _template(name, **values):
    with open(os.path.join(WEB_DIR, name), encoding="utf-8") as f:
        text = f.read()
    for k, v in values.items():
        text = text.replace("{{%s}}" % k, v)
    return text


class Handler(BaseHTTPRequestHandler):
    server_version = "OAMock"

    def log_message(self, *args):
        pass

    # Only answer requests addressed to this server (blocks DNS-rebinding pages).
    def _host_ok(self):
        port = self.server.server_address[1]
        return self.headers.get("Host", "") in ("127.0.0.1:%d" % port, "localhost:%d" % port)

    def _send(self, code, body, ctype, cache="no-cache"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(b)

    def _not_found(self):
        self._send(404, "not found", "text/plain; charset=utf-8")

    def _token_ok(self):
        return self._host_ok() and self.headers.get("X-Token") == TOKEN

    def _json(self, code, obj):
        self._send(code, json.dumps(obj), "application/json")

    def _body(self):
        if "application/json" not in self.headers.get("Content-Type", ""):
            raise submissions.BadRequest("expected JSON")
        n = int(self.headers.get("Content-Length", "0"))
        if n > 2 * 1024 * 1024:
            raise submissions.BadRequest("request too large")
        return json.loads(self.rfile.read(n) or b"{}")

    def _submissions(self, method, parts, query):
        """/api/submissions[/<company>/<qid>/<id>]"""
        if not self._token_ok():
            return self._json(403, {"error": "forbidden"})
        try:
            if method == "GET" and not parts:
                q = parse_qs(query)
                one = lambda k: (q.get(k) or [None])[0]
                return self._json(200, submissions.listing(one("company"), one("qid"), int(one("limit") or 200)))
            if method == "GET" and len(parts) == 3:
                hit = submissions.read(*parts)
                return self._json(200, hit) if hit else self._json(404, {"error": "not found"})
            if method == "POST" and not parts:
                return self._json(200, submissions.save(self._body()))
            if method == "DELETE" and len(parts) == 3:
                return self._json(200, {"deleted": submissions.delete(*parts)})
        except (submissions.BadRequest, ValueError) as e:
            return self._json(400, {"error": str(e)})
        except OSError as e:
            return self._json(500, {"error": "could not access %s: %s" % (submissions.SUB_DIR, e)})
        return self._json(404, {"error": "not found"})

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, "forbidden", "text/plain")
        url = urlsplit(self.path)
        path = url.path
        parts = [p for p in path.split("/") if p]

        if parts[:2] == ["api", "submissions"]:
            return self._submissions("GET", parts[2:], url.query)

        if not parts:
            links = "".join('<a class="company" href="/%s">%s<small>%s</small></a>' % (k, html.escape(n), html.escape(t))
                            for k, n, t in data.companies())
            return self._send(200, _template("index.html", companies=links, token=json.dumps(TOKEN)), "text/html; charset=utf-8")

        if parts[:2] == ["api", "library"]:
            if not self._token_ok():
                return self._json(403, {"error": "forbidden"})
            if parts[2:] == ["job"]:
                return self._json(200, library.job())
            if not parts[2:]:
                return self._json(200, library.listing())
            return self._not_found()

        if parts[0] == "static":
            return self._static(parts[1:])

        if parts[0] == "api":
            if parts[1:] == ["companies"]:
                body = json.dumps([{"key": k, "name": n, "tagline": t} for k, n, t in data.companies()])
                return self._send(200, body, "application/json")
            if len(parts) == 4 and parts[1] == "companies" and parts[3] == "data.js":
                js = data.as_script(parts[2])
                return self._send(200, js, "text/javascript; charset=utf-8") if js else self._not_found()
            if len(parts) == 6 and parts[1] == "companies" and parts[3] == "questions" and parts[5] == "tests":
                q = data.question(parts[2], parts[4])
                return self._json(200, {"hidden": q.get("hidden", [])}) if q else self._not_found()
            return self._not_found()

        if parts == ["favicon.ico"]:
            return self._send(204, b"", "image/x-icon")

        if len(parts) == 1:
            p = data.load(parts[0])
            if p is None:
                return self._not_found()
            page = _template("app.html", title=html.escape(p["config"].get("name", parts[0])),
                             token=json.dumps(TOKEN), company=parts[0])
            return self._send(200, page, "text/html; charset=utf-8")
        self._not_found()

    def _static(self, parts):
        if not parts or any(p in ("..", ".") or p.startswith(".") for p in parts):
            return self._not_found()
        full = os.path.realpath(os.path.join(STATIC_DIR, *parts))
        if not full.startswith(os.path.realpath(STATIC_DIR) + os.sep) or not os.path.isfile(full):
            return self._not_found()
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/"):
            ctype += "; charset=utf-8"
        with open(full, "rb") as f:
            self._send(200, f.read(), ctype)

    def do_DELETE(self):
        parts = [p for p in urlsplit(self.path).path.split("/") if p]
        if parts[:2] != ["api", "submissions"]:
            return self._json(404, {"error": "not found"})
        self._submissions("DELETE", parts[2:], "")

    def do_POST(self):
        if urlsplit(self.path).path == "/api/submissions":
            return self._submissions("POST", [], "")
        if urlsplit(self.path).path == "/api/library":
            if not self._token_ok():
                return self._json(403, {"error": "forbidden"})
            try:
                req = self._body()
                return self._json(200, library.start(str(req.get("action", "")), req.get("company")))
            except (ValueError, submissions.BadRequest) as e:
                return self._json(400, {"error": str(e)})
        if urlsplit(self.path).path == "/api/grade":
            if not self._token_ok():
                return self._json(403, {"error": "forbidden"})
            try:
                req = self._body()
                return self._json(200, grading.grade(req.get("company"), req.get("qid"), req.get("lang"), req.get("code", ""),
                                                     "all" if req.get("scope") == "all" else "samples"))
            except (grading.GradeError, submissions.BadRequest, ValueError) as e:
                return self._json(400, {"error": str(e)})
        if (self.path != "/run" or not self._host_ok() or self.headers.get("X-Token") != TOKEN
                or "application/json" not in self.headers.get("Content-Type", "")):
            return self._send(403, '{"error":"forbidden"}', "application/json")
        try:
            n = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(n) or b"{}")
            res = judge.judge(req.get("lang"), req.get("code", ""), list(req.get("inputs", []))[:MAX_INPUTS],
                              float(req.get("limit", 2000)))
        except Exception as e:
            res = {"compile_error": "Runner error: %s" % e}
        self._send(200, json.dumps(res), "application/json")


def serve(port, tries=20):
    """Bind to 127.0.0.1:port, or the next free port. Returns the server."""
    for p in range(port, port + tries):
        try:
            return ThreadingHTTPServer(("127.0.0.1", p), Handler)
        except OSError:
            if p == port:
                print("\nPort %d is busy. An older copy may still be running (Ctrl+Z only pauses it)." % p)
                print("Stop it with  kill %%1  or  lsof -ti tcp:%d | xargs kill . Trying the next port..." % p)
    raise SystemExit("No free port between %d and %d." % (port, port + tries - 1))
