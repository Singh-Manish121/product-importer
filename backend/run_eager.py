"""Run integration flow locally with Celery eager mode and a local webhook listener.

This script will:
- Enable Celery eager execution (tasks run synchronously)
- Start a simple HTTP server on port 9000 to receive webhook POSTs and print them
- Create DB tables
- Create a webhook that listens to product.created and product.updated
- Create a temporary CSV and a Job record
- Enqueue the import task (it will run inline), which will create/update products and schedule webhook deliveries

Run from the `backend` folder using the venv Python.
"""
import threading
import time
import json
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from uuid import uuid4

from app.celery_app import celery_app
import app.tasks as tasks_module
from app.database import Base, engine, SessionLocal
from app.models import Webhook, Job, JobStatus

# Enable eager mode so send_task executes tasks synchronously
celery_app.conf.task_always_eager = True


class EchoHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(length)
        try:
            print('\n[Webhook Listener] Received POST:')
            parsed = json.loads(body)
            print(json.dumps(parsed, indent=2))
        except Exception:
            print(body)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')


def start_listener(host='0.0.0.0', port=9000):
    server = HTTPServer((host, port), EchoHandler)
    print(f'[Webhook Listener] Listening on http://{host}:{port}')
    server.serve_forever()


def main():
    # Start webhook listener in background
    t = threading.Thread(target=start_listener, daemon=True)
    t.start()
    time.sleep(0.5)

    # Ensure DB tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Create a webhook that points to our local listener
    wh = Webhook(
        url='http://127.0.0.1:9000/webhook',
        event_types=['product.created', 'product.updated'],
        enabled=True,
    )
    db.add(wh)
    db.commit()
    db.refresh(wh)
    print(f'[Setup] Created webhook id={wh.id} -> {wh.url} events={wh.event_types}')

    # Create a temporary CSV file with test rows
    tmp = Path(tempfile.gettempdir()) / f'test_products_{uuid4().hex}.csv'
    with open(tmp, 'w', encoding='utf-8', newline='') as f:
        f.write('sku,name,description\n')
        f.write('PROD-EAGER-1,Product Eager 1,First eager product\n')
        f.write('PROD-EAGER-2,Product Eager 2,Second eager product\n')
        f.write('PROD-EAGER-1,Product Eager 1 Updated,Updated description\n')
    print(f'[Setup] Wrote test CSV: {tmp}')

    # Create Job record
    job_uuid = str(uuid4())
    job = Job(
        job_id=job_uuid,
        status=JobStatus.PENDING,
        filename=str(tmp),
        total_rows=0,
        processed_rows=0,
        created_rows=0,
        updated_rows=0,
        failed_rows=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    print(f'[Setup] Created Job id={job.job_id} filename={job.filename}')

    # Replace celery_app.send_task with an eager runner that calls tasks directly
    def eager_send_task(name, args=None, kwargs=None, **opts):
        args = args or []
        kwargs = kwargs or {}
        if name == 'app.tasks.import_csv':
            # call import_csv task function directly
            return tasks_module.import_csv(*args, **kwargs)
        if name == 'app.tasks.deliver_webhook':
            return tasks_module.deliver_webhook(*args, **kwargs)
        raise RuntimeError(f'Unknown task: {name}')

    celery_app.send_task = eager_send_task

    # Enqueue (actually runs inline via eager_send_task)
    print('[Run] Enqueuing import task (runs eagerly via in-process send_task)...')
    res = celery_app.send_task('app.tasks.import_csv', args=[job.job_id, str(tmp)])
    print('[Run] Task result:', res)

    # Give a moment for the webhook listener to print deliveries
    time.sleep(1)

    # Inspect DB products
    from app.models import Product
    prods = db.query(Product).all()
    print(f'[Result] Products in DB: {len(prods)}')
    for p in prods:
        print(f' - {p.id}: {p.sku} | {p.name} | {p.description}')

    # Cleanup temp CSV
    try:
        tmp.unlink()
    except Exception:
        pass

    print('\n[Done] Eager run complete.')


if __name__ == '__main__':
    main()
