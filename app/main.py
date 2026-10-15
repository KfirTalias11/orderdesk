import time
import uuid
import psycopg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.db import connection, queue
from app.logging import event
from app.orders import OrderInput, create_order, list_orders

app = FastAPI(title='OrderDesk API', version='1.0.0', docs_url=None, redoc_url=None,
              openapi_url='/api/openapi.json')


@app.middleware('http')
async def request_log(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.monotonic()
    response = await call_next(request)
    response.headers['X-Request-ID'] = request_id
    event('http.request', request_id=request_id, method=request.method, path=request.url.path,
          status=response.status_code, duration_ms=round((time.monotonic()-start)*1000))
    return response


@app.exception_handler(psycopg.Error)
async def database_error(request, exc):
    event('dependency.failed', dependency='postgres', error_type=type(exc).__name__)
    return JSONResponse(status_code=503, content={'detail': 'Database unavailable. Please try again.'})


@app.get('/api/health/live')
def live():
    return {'status': 'alive'}


def dependencies():
    state = {}
    for name, check in [('postgres', lambda: check_database()), ('redis', lambda: queue().ping())]:
        try:
            check()
            state[name] = 'available'
        except Exception as exc:
            state[name] = 'unavailable'
            event('dependency.failed', dependency=name, error_type=type(exc).__name__)
    return state


def check_database():
    with connection() as db:
        db.execute('SELECT id FROM products LIMIT 1')


@app.get('/api/health/ready')
def ready():
    state = dependencies()
    healthy = all(value == 'available' for value in state.values())
    return JSONResponse(status_code=200 if healthy else 503,
                        content={'status': 'ready' if healthy else 'degraded', 'dependencies': state})


@app.get('/api/products')
def products():
    with connection() as db:
        return db.execute('SELECT * FROM products ORDER BY id').fetchall()


@app.get('/api/orders')
def orders():
    return list_orders()


@app.post('/api/orders', status_code=201)
def place_order(data: OrderInput):
    return create_order(data)


@app.get('/api/status')
def status():
    deps = dependencies()
    with connection() as db:
        worker = db.execute("SELECT *, heartbeat_at > now()-interval '15 seconds' AS fresh FROM worker_status WHERE name='fulfillment'").fetchone()
        summary = db.execute("SELECT count(*) AS orders, count(*) FILTER (WHERE status='pending') AS pending, COALESCE(sum(total_cents),0) AS revenue_cents FROM orders").fetchone()
    return {'dependencies': deps, 'summary': summary,
            'worker': {'state': 'running' if worker and worker['fresh'] else 'stale',
                       'heartbeat_at': worker['heartbeat_at'] if worker else None,
                       'last_success_at': worker['last_success_at'] if worker else None}}
