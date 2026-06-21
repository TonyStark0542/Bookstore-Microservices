# Bookstore-Microservices

A three-tier bookstore application (Flask backend, Flask frontend, MongoDB) built to practice containerization and CI/CD, going from a single monolithic app to a microservices setup deployed through an automated Jenkins pipeline.

## What this project covers

I built this to get hands-on with the full path from code to a running deployment, not just the application itself. That meant:

- Splitting the app into a **backend** service (API + MongoDB + Gemini AI integration for book summaries) and a **frontend** service (renders pages, proxies API calls to the backend) — two independent containers talking over a Docker bridge network.
- Writing a **multi-stage Dockerfile** for each service, so build-time dependencies don't bloat the final runtime image.
- Provisioning the **Jenkins server itself with Terraform** — a Compute Engine VM with a startup script that installs Jenkins, Docker, and Docker Compose automatically, plus a firewall rule opening the ports needed for the Jenkins UI and the app.
- Building a **Jenkins pipeline** that validates the environment before doing anything, builds the containers, injects the Gemini API key securely from Jenkins credentials, and brings the stack up with `docker compose`.
- Writing a **pre-flight check script** (`deploy_check.sh`) that the pipeline runs first — it checks Docker is installed and running, Docker Compose is available, the required API key is set, and the expected files exist. If any of that fails, the pipeline stops immediately instead of failing halfway through a build.

## Architecture

```
                     ┌──────────────────┐
                     │   Jenkins (VM)   │
                     │  provisioned by  │
                     │    Terraform     │
                     └────────┬─────────┘
                              │ runs pipeline
                              ▼
        ┌─────────────────────────────────────────┐
        │            docker-compose stack         │
        │                                         │
        │  ┌──────────────┐      ┌───────────────┐│
        │  │   Frontend   │ ───► │    Backend    ││
        │  │ (Flask :5000)│      │ (Flask :8000) ││
        │  └──────────────┘      └───────┬───────┘│
        │                                 │       │
        │                          ┌──────▼──────┐│
        │                          │   MongoDB   ││
        │                          └─────────────┘│
        └─────────────────────────────────────────┘
```

## Pipeline stages

1. **Pre-Flight Validation** — runs `deploy_check.sh` to confirm Docker, Docker Compose, the Gemini API key, and required files are all in place before touching anything else.
2. **Docker Build** — builds both service images using `docker compose build`.
3. **Secure Config** — pulls the Gemini API key from Jenkins credentials and writes it to a `.env` file at deploy time, so the key never appears in source control or build logs.
4. **Launch & Seed** — tears down any old containers, brings the stack up with `docker compose up -d`, and restores the MongoDB backup so the app has data to serve.
5. **Cleanup** — clears the Jenkins workspace after every run, pass or fail.

## Folder structure
 
```
backend/              # Flask API, MongoDB connection, Gemini integration, Dockerfile
frontend/             # Flask app serving pages, proxies requests to backend, Dockerfile
Jenkinsfile           # Pipeline definition
deploy_check.sh       # Pre-flight environment validation script
docker-compose.yml
main.tf               # Terraform config — provisions the Jenkins VM, firewall, and bootstrap script
```

## Tech used

Docker, Docker Compose, Jenkins, Terraform, Flask, MongoDB, Google Gemini API, GCP Compute Engine


## Running it locally

```bash
# 1. Make sure Docker is installed and GEMINI_API_KEY is set in your environment
export GEMINI_API_KEY=your_key_here

# 2. Build and start the stack
docker compose up -d --build

# 3. Seed the database
docker exec -it mongodb-backend mongorestore --archive=/backup/db_backup.archive --gzip

# 4. Stop everything
docker compose down
```

## What I'd improve next

- Move from Jenkins shell scripting to a declarative pipeline with proper stage gates for testing.
- Add a GitHub Actions workflow as an alternative to Jenkins, since it's more commonly used in modern stacks.
- Add basic integration tests before the build stage instead of just environment checks.
