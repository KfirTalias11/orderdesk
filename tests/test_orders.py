import pytest
from fastapi.testclient import TestClient


def client():
    from app.main import app
    return TestClient(app)


def test_order_is_persisted_with_server_price_and_outbox():
    from app.db import connection
    c = client()
    product = c.get('/api/products').json()[0]
    response = c.post('/api/orders', json={'customer_name': 'Ada Studio', 'product_id': product['id'], 'quantity': 2})
    assert response.status_code == 201
    order = response.json()
    assert order['total_cents'] == 4800
    assert order['status'] == 'pending'
    assert any(row['id'] == order['id'] for row in c.get('/api/orders').json())
    with connection() as db:
        assert db.execute('SELECT count(*) AS n FROM outbox WHERE order_id=%s', (order['id'],)).fetchone()['n'] == 1


@pytest.mark.parametrize('patch', [{'quantity': 0}, {'quantity': -1}, {'quantity': 1001}, {'quantity': True}, {'customer_name': '   '}, {'customer_name': 'x' * 121}])
def test_invalid_order_never_inserts(patch):
    from app.db import connection
    with connection() as db:
        before = db.execute('SELECT count(*) AS n FROM orders').fetchone()['n']
    payload = {'customer_name': 'Ada', 'product_id': 1, 'quantity': 1, **patch}
    assert client().post('/api/orders', json=payload).status_code == 422
    with connection() as db:
        assert db.execute('SELECT count(*) AS n FROM orders').fetchone()['n'] == before


def test_unknown_product_is_rejected():
    assert client().post('/api/orders', json={'customer_name': 'Ada', 'product_id': 999999, 'quantity': 1}).status_code == 404


def test_client_cannot_set_price():
    assert client().post('/api/orders', json={'customer_name': 'Ada', 'product_id': 1, 'quantity': 1, 'total_cents': 1}).status_code == 422
