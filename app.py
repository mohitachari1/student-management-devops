"""Student Management System - Flask app with built-in Prometheus metrics."""
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify, g, Response

app = Flask(__name__)

# In-memory store (kept simple: the focus of this project is DevOps automation)
students = {}
_next_id = 1

# ---------------- Prometheus metrics (no external library needed) ----------------
START_TIME = time.time()
request_counts = {}      # (method, endpoint, status) -> count
latency_sum = {}         # endpoint -> total seconds
latency_count = {}       # endpoint -> number of requests


@app.before_request
def _start_timer():
    g.t0 = time.time()


@app.after_request
def _record_metrics(resp):
    if request.path != "/metrics":
        ep = request.endpoint or "unknown"
        key = (request.method, ep, resp.status_code)
        request_counts[key] = request_counts.get(key, 0) + 1
        latency_sum[ep] = latency_sum.get(ep, 0.0) + (time.time() - g.t0)
        latency_count[ep] = latency_count.get(ep, 0) + 1
    return resp


@app.route("/metrics")
def metrics():
    lines = [
        "# HELP app_up Application is up (1 = up).",
        "# TYPE app_up gauge",
        "app_up 1",
        "# HELP app_uptime_seconds Seconds since app start.",
        "# TYPE app_uptime_seconds gauge",
        f"app_uptime_seconds {time.time() - START_TIME:.2f}",
        "# HELP app_students_total Number of students stored.",
        "# TYPE app_students_total gauge",
        f"app_students_total {len(students)}",
        "# HELP http_requests_total Total HTTP requests.",
        "# TYPE http_requests_total counter",
    ]
    for (m, ep, st), c in sorted(request_counts.items()):
        lines.append(f'http_requests_total{{method="{m}",endpoint="{ep}",status="{st}"}} {c}')
    lines += [
        "# HELP http_request_duration_seconds_sum Total request time.",
        "# TYPE http_request_duration_seconds_sum counter",
    ]
    for ep, s in sorted(latency_sum.items()):
        lines.append(f'http_request_duration_seconds_sum{{endpoint="{ep}"}} {s:.6f}')
    lines += [
        "# HELP http_request_duration_seconds_count Request count for latency.",
        "# TYPE http_request_duration_seconds_count counter",
    ]
    for ep, c in sorted(latency_count.items()):
        lines.append(f'http_request_duration_seconds_count{{endpoint="{ep}"}} {c}')
    return Response("\n".join(lines) + "\n", mimetype="text/plain; version=0.0.4")


# ---------------- Web UI ----------------
@app.route("/")
def index():
    return render_template("index.html", count=len(students))


@app.route("/students")
def list_students():
    return render_template("students.html", students=students.values())


@app.route("/add", methods=["GET", "POST"])
def add_student():
    global _next_id
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template("add_student.html", error="Name is required"), 400
        students[_next_id] = {
            "id": _next_id,
            "name": name,
            "email": request.form.get("email", "").strip(),
            "course": request.form.get("course", "").strip(),
        }
        _next_id += 1
        return redirect(url_for("list_students"))
    return render_template("add_student.html", error=None)


@app.route("/edit/<int:sid>", methods=["GET", "POST"])
def edit_student(sid):
    s = students.get(sid)
    if not s:
        return "Student not found", 404
    if request.method == "POST":
        s["name"] = request.form.get("name", s["name"]).strip() or s["name"]
        s["email"] = request.form.get("email", s["email"]).strip()
        s["course"] = request.form.get("course", s["course"]).strip()
        return redirect(url_for("list_students"))
    return render_template("add_student.html", error=None, student=s)


@app.route("/delete/<int:sid>", methods=["POST"])
def delete_student(sid):
    students.pop(sid, None)
    return redirect(url_for("list_students"))


# ---------------- REST API (for Postman / API tests) ----------------
@app.route("/api/students", methods=["GET"])
def api_list():
    return jsonify(list(students.values()))


@app.route("/api/students", methods=["POST"])
def api_add():
    global _next_id
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify(error="name is required"), 400
    s = {"id": _next_id, "name": data["name"],
         "email": data.get("email", ""), "course": data.get("course", "")}
    students[_next_id] = s
    _next_id += 1
    return jsonify(s), 201


@app.route("/api/students/<int:sid>", methods=["GET"])
def api_get(sid):
    s = students.get(sid)
    return (jsonify(s), 200) if s else (jsonify(error="not found"), 404)


@app.route("/api/students/<int:sid>", methods=["PUT"])
def api_update(sid):
    s = students.get(sid)
    if not s:
        return jsonify(error="not found"), 404
    data = request.get_json(silent=True) or {}
    s.update({k: data[k] for k in ("name", "email", "course") if k in data})
    return jsonify(s)


@app.route("/api/students/<int:sid>", methods=["DELETE"])
def api_delete(sid):
    if sid not in students:
        return jsonify(error="not found"), 404
    del students[sid]
    return "", 204


@app.route("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
