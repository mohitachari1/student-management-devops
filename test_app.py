import pytest
import app as app_module


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    app_module.students.clear()
    app_module._next_id = 1
    with app_module.app.test_client() as c:
        yield c


# ---------- Unit / UI tests ----------
def test_home_page(client):
    assert client.get("/").status_code == 200


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.get_json()["status"] == "ok"


def test_add_student_form(client):
    r = client.post("/add", data={"name": "Asha", "email": "a@x.com", "course": "CS"})
    assert r.status_code == 302
    assert b"Asha" in client.get("/students").data


def test_add_student_requires_name(client):
    assert client.post("/add", data={"name": ""}).status_code == 400


def test_edit_and_delete_student(client):
    client.post("/add", data={"name": "Ravi"})
    client.post("/edit/1", data={"name": "Ravi K", "email": "", "course": "IT"})
    assert b"Ravi K" in client.get("/students").data
    client.post("/delete/1")
    assert b"Ravi K" not in client.get("/students").data


def test_edit_missing_student(client):
    assert client.get("/edit/99").status_code == 404


# ---------- API tests (GET / POST / PUT / DELETE) ----------
def test_api_post_and_get(client):
    r = client.post("/api/students", json={"name": "Meera", "course": "AI"})
    assert r.status_code == 201
    assert client.get("/api/students").get_json()[0]["name"] == "Meera"
    assert client.get("/api/students/1").status_code == 200


def test_api_post_validation(client):
    assert client.post("/api/students", json={}).status_code == 400


def test_api_put(client):
    client.post("/api/students", json={"name": "A"})
    r = client.put("/api/students/1", json={"name": "B"})
    assert r.get_json()["name"] == "B"


def test_api_delete(client):
    client.post("/api/students", json={"name": "A"})
    assert client.delete("/api/students/1").status_code == 204
    assert client.get("/api/students/1").status_code == 404


# ---------- Monitoring ----------
def test_metrics_endpoint(client):
    client.get("/")
    body = client.get("/metrics").get_data(as_text=True)
    assert "app_up 1" in body
    assert "http_requests_total" in body
