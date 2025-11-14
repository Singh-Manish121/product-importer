#!/usr/bin/env python3
"""
Run the app in eager mode: Celery tasks execute synchronously in-process.
No Redis broker needed. Perfect for local development and testing.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Monkey-patch Celery to use eager execution
from app.celery_app import celery_app
celery_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,
    broker_url='memory://',
    result_backend='cache+memory://',
)

# Now run the app
if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("Starting Product Importer in EAGER mode")
    print("Celery tasks will execute synchronously (no Redis needed)")
    print("=" * 60 + "\n")
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
