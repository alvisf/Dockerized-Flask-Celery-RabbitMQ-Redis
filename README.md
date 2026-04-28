# Dockerized Flask + Celery + RabbitMQ + Redis

A reference stack for asynchronous task processing with Flask and Celery, fully containerized with Docker Compose.

Upload an image → a Celery worker crops and resizes it to 300×300 → the result is displayed in the browser.

## Architecture

```
Browser → Flask (web) → RabbitMQ (broker) → Celery (worker) → Redis (result backend)
```

## Quick Start

```bash
docker compose up --build
```

Open http://localhost:5000

## Configuration

Environment variables (set in `.env` or export):

| Variable | Default |
|---|---|
| `RABBITMQ_USER` | `admin` |
| `RABBITMQ_PASS` | `mypass` |

## Stack

- **Python 3.12** / Flask 3.x
- **Celery 5.4** with msgpack serialization
- **RabbitMQ 3** (broker) with management UI
- **Redis 7** (result backend)
- **Pillow 11** for image processing
- **Bootstrap 5** frontend

## Project Structure

```
├── app/
│   ├── app.py          # Flask routes
│   ├── tasks.py        # Celery tasks
│   └── templates/
│       ├── index.html   # Upload form
│       └── download.html # Progress + result
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Blog Post

📝 [Dockerized Flask Celery RabbitMQ Redis Application](https://levelup.gitconnected.com/dockerized-flask-celery-rabbitmq-redis-application-df74c837a0a1) — Medium / Level Up Coding
