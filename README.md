# Student Management System - End-to-End DevOps Pipeline

Flask CRUD app delivered through: **GitHub -> Jenkins (build, test) -> Docker -> Docker Hub -> Deploy -> Prometheus -> Grafana -> Alerting**.

## Architecture
Developer -> Git/GitHub -> (webhook) Jenkins -> Build -> PyTest -> Docker Build -> Docker Hub -> Deploy container
-> Prometheus (scrapes app `/metrics` + node-exporter) -> Grafana dashboard -> Alert rules

## 1. Run locally
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest -v
python app.py            # http://localhost:5000
```

## 2. Docker
```bash
docker build -t student-app .
docker run -p 5000:5000 student-app
```

## 3. Git / GitHub
```bash
git init
git add .
git commit -m "Initial application"
git branch -M main
git remote add origin https://github.com/<user>/student-management-devops.git
git push -u origin main
```

## 4. Jenkins setup
1. Run Jenkins (it needs Python 3, Docker CLI and access to the Docker socket on the same host).
2. Plugins: Git, Pipeline, GitHub, Credentials Binding, JUnit.
3. Add credentials: *Username with password*, ID `dockerhub-creds` (Docker Hub login).
4. New Item -> Pipeline -> "Pipeline script from SCM" -> your GitHub repo, script path `Jenkinsfile`.
5. Edit `DOCKERHUB_USER` in the Jenkinsfile.
6. Build Triggers -> tick "GitHub hook trigger for GITScm polling".
7. GitHub repo -> Settings -> Webhooks -> `http://<jenkins-host>:8080/github-webhook/` (content type JSON, push events).
   (On localhost, expose Jenkins with ngrok.)

## 5. Monitoring stack
```bash
docker network create devops-net       # once; Jenkins deploys the app onto this network
docker compose up -d                   # Prometheus :9090, Grafana :3000 (admin/admin), node-exporter :9100
```
- Prometheus -> Status -> Targets: `student-app`, `node`, `prometheus` should be UP.
- Grafana -> Dashboards -> "DevOps Pipeline - Student App" (auto-provisioned): CPU, memory, disk, network,
  availability, request rate, latency, students stored.
- Alerts: Prometheus -> Alerts (`HighCPUUsage`, `ApplicationDown`).

## 6. Final demo (viva)
1. Change `templates/index.html`, then `git commit` and `git push`.
2. Jenkins starts automatically -> Build SUCCESS -> Tests PASS -> Docker image pushed -> container deployed.
3. Open http://localhost:5000.
4. Show Grafana dashboards.
5. Trigger the CPU alert: `docker run --rm -d --name stress progrium/stress --cpu 4 --timeout 180s`
   (wait ~1-2 min; Prometheus -> Alerts -> HighCPUUsage = FIRING).
6. Trigger the DOWN alert: `docker stop student-app` (ApplicationDown fires after 30 s).
7. Show "don't deploy if tests fail": break a test, push, and show Jenkins stopping at the Test stage.

## API (Postman)
`GET/POST /api/students`, `GET/PUT/DELETE /api/students/<id>`, `GET /health`, `GET /metrics`
