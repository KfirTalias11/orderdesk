from fastapi.testclient import TestClient


def test_live_and_ready_are_separate(monkeypatch):
    from app.main import app
    c = TestClient(app)
    assert c.get('/api/health/ready').status_code == 200
    monkeypatch.setenv('DATABASE_URL', 'postgresql://nobody:private-value@127.0.0.1:1/missing')
    assert c.get('/api/health/live').status_code == 200
    response = c.get('/api/health/ready')
    assert response.status_code == 503
    assert 'private-value' not in response.text
    assert c.get('/api/orders').status_code == 503


def test_redis_failure_is_visible(monkeypatch):
    from app.main import app
    monkeypatch.setenv('REDIS_URL', 'redis://127.0.0.1:1/0')
    response = TestClient(app).get('/api/health/ready')
    assert response.status_code == 503
    assert response.json()['dependencies']['redis'] == 'unavailable'


def test_stale_worker_is_not_reported_healthy():
    from app.main import app
    from app.db import connection
    with connection() as db:
        db.execute("INSERT INTO worker_status (name,heartbeat_at) VALUES ('fulfillment',now()-interval '2 minutes') ON CONFLICT (name) DO UPDATE SET heartbeat_at=excluded.heartbeat_at")
    assert TestClient(app).get('/api/status').json()['worker']['state'] == 'stale'
