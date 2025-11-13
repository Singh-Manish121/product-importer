# Product Importer - Full Stack Application

A scalable CSV product import system with real-time progress tracking, product management, and webhook delivery.

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Async Tasks**: Celery + Redis
- **Frontend**: React + Vite (to be created)
- **Database**: PostgreSQL
- **Message Broker**: Redis

## Project Structure

```
product-importer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Settings
│   │   ├── database.py             # SQLAlchemy setup
│   │   ├── celery_app.py           # Celery config
│   │   ├── models/                 # Data models (to be created)
│   │   ├── routers/                # API endpoints
│   │   ├── tasks/                  # Celery tasks (to be created)
│   │   └── services/               # Business logic (to be created)
│   ├── migrations/                 # Alembic migrations
│   ├── tests/                      # Unit tests
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Environment variables template
│   ├── docker-compose.yml          # Local dev containers
│   ├── alembic.ini                 # Alembic config
│   └── manage.py                   # Dev management script
├── frontend/
│   ├── src/
│   │   ├── components/             # React components
│   │   ├── pages/                  # Page components
│   │   ├── App.jsx                 # Main app component
│   │   └── main.jsx                # Entry point
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Prerequisites

- **Python 3.9+** (with pip, venv)
- **Node.js 18+** (with npm) for frontend
- **Docker & Docker Compose** (for Postgres + Redis)
- **Git** (for version control)

## Backend Setup

### Step 1: Install dependencies

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Start Postgres & Redis (using Docker)

Ensure Docker is running, then:

```powershell
docker-compose up -d
```

Verify services are running:
```powershell
docker ps
```

You should see `product_postgres` and `product_redis` containers.

### Step 3: Configure environment

Copy the example `.env` file and create a local `.env`:

```powershell
copy .env.example .env
```

Review the `.env` file. Default values should work for local development:
- `DATABASE_URL`: PostgreSQL connection (default: `postgresql://product_user:product_pass@localhost:5432/product_db`)
- `REDIS_URL`: Redis connection (default: `redis://localhost:6379`)

### Step 4: Run database migrations

```powershell
python manage.py migrate
```

This creates tables in PostgreSQL using Alembic.

### Step 5: Start the development server

In a new terminal (with venv activated):

```powershell
python manage.py runserver
```

The API should be available at **http://localhost:8000**

API documentation (Swagger UI) is at **http://localhost:8000/docs**

### Step 6: Start the Celery worker (in another terminal)

```powershell
python manage.py worker
```

You should see logs indicating the worker is listening for tasks.

## Frontend Setup

### Step 1: Initialize React + Vite project

```powershell
cd frontend
npm create vite@latest . -- --template react
npm install
```

### Step 2: Start development server

```powershell
npm run dev
```

Frontend should be available at **http://localhost:5173**

## Running the Full Stack Locally

### Terminal 1: Backend Server
```powershell
cd backend
venv\Scripts\activate
python manage.py runserver
```

### Terminal 2: Celery Worker
```powershell
cd backend
venv\Scripts\activate
python manage.py worker
```

### Terminal 3: Frontend Dev Server
```powershell
cd frontend
npm run dev
```

### Terminal 4: Docker Services (if not running)
```powershell
cd backend
docker-compose up -d
```

## Testing

### Run backend tests

```powershell
cd backend
python manage.py test
```

Or directly with pytest:

```powershell
cd backend
pytest tests/ -v
```

## API Health Check

Once the server is running:

```powershell
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Cleaning Up

To stop Docker services:

```powershell
cd backend
docker-compose down
```

To remove volumes (resets database):

```powershell
cd backend
docker-compose down -v
```

## Commits

Each feature will be committed with a clear commit message:
- `git add .`
- `git commit -m "Task 1: Project scaffolding and backend setup"`

View commit history:
```powershell
git log --oneline
```

## Next Steps

We will implement the following features one-by-one:

1. ✅ **Task 1**: Project scaffolding (current) — basic FastAPI app, Celery config, health check
2. **Task 2**: Database models & migrations (Product, Webhook, Job)
3. **Task 3**: Product CRUD APIs + basic UI
4. **Task 4**: CSV upload endpoint + job tracking
5. **Task 5**: SSE progress streaming + UI progress bar
6. **Task 6**: CSV import worker (bulk insert with upsert)
7. **Task 7**: Bulk delete implementation
8. **Task 8**: Webhook management + delivery
9. **Task 9**: Tests + CI/CD
10. **Task 10**: Deployment configuration

---

**Last Updated**: November 13, 2025