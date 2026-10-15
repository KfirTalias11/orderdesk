import pytest
from fastapi.testclient import TestClient


def new_order():
    from app.main import app
    return TestClient(app).post('/api/orders', json={'customer_name': 'Worker test', 'product_id': 1, 'quantity': 1}).json()['id']


def test_fulfillment_is_idempotent():
    from app.worker import fulfill_order
    from app.db import connection
    order_id = new_order()
    assert fulfill_order(order_id) is True
    assert fulfill_order(order_id) is False
    with connection() as db:
        assert db.execute('SELECT status FROM orders WHERE id=%s', (order_id,)).fetchone()['status'] == 'fulfilled'
        assert db.execute('SELECT completed_at FROM outbox WHERE order_id=%s', (order_id,)).fetchone()['completed_at'] is not None


def test_queue_failure_does_not_lose_order(monkeypatch):
    from app.worker import dispatch_pending, fulfill_order
    from app.db import connection, queue
    order_id = new_order()
    with monkeypatch.context() as patch:
        patch.setenv('REDIS_URL', 'redis://127.0.0.1:1/0')
        with pytest.raises(Exception):
            dispatch_pending()
    dispatch_pending()
    received = []
    while item := queue().lpop('orders:fulfillment'):
        received.append(int(item))
    assert order_id in received
    # Simulate loss after dequeue: durable unfinished entry must be redelivered.
    with connection() as db:
        db.execute("UPDATE outbox SET dispatched_at=now()-interval '1 minute' WHERE order_id=%s", (order_id,))
    dispatch_pending()
    assert str(order_id) in queue().lrange('orders:fulfillment', 0, -1)
    assert fulfill_order(order_id)
