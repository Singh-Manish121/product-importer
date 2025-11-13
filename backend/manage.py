#!/usr/bin/env python
"""Development management script."""
import sys
import subprocess
from app.config import get_settings

settings = get_settings()


def run_migrations():
    """Run database migrations."""
    print("Running migrations...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd="backend",
    )
    return result.returncode


def create_migration(message):
    """Create a new migration."""
    if not message:
        print("Usage: python manage.py makemigrations <message>")
        return 1
    print(f"Creating migration: {message}")
    result = subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", message],
        cwd="backend",
    )
    return result.returncode


def runserver():
    """Start the development server."""
    print("Starting development server...")
    print("API docs available at http://localhost:8000/docs")
    result = subprocess.run(
        ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd="backend",
    )
    return result.returncode


def run_worker():
    """Start the Celery worker."""
    print("Starting Celery worker...")
    result = subprocess.run(
        ["celery", "-A", "app.celery_app", "worker", "--loglevel=info"],
        cwd="backend",
    )
    return result.returncode


def run_tests():
    """Run tests."""
    print("Running tests...")
    result = subprocess.run(
        ["pytest", "tests/", "-v"],
        cwd="backend",
    )
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
Usage:
  python manage.py runserver     - Start development server
  python manage.py migrate       - Run database migrations
  python manage.py makemigrations <message> - Create a migration
  python manage.py worker        - Start Celery worker
  python manage.py test          - Run tests
        """)
        sys.exit(1)

    command = sys.argv[1]
    
    if command == "runserver":
        sys.exit(runserver())
    elif command == "migrate":
        sys.exit(run_migrations())
    elif command == "makemigrations":
        message = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        sys.exit(create_migration(message))
    elif command == "worker":
        sys.exit(run_worker())
    elif command == "test":
        sys.exit(run_tests())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
