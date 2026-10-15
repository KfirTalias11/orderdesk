"""Exercise the gateway, order API, persistence, queue and fulfillment."""
import json
import sys
import time
from urllib.request import Request, urlopen

base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8088'

def request(path, data=None):
    body = json.dumps(data).encode() if data else None
    with urlopen(Request(base + '/api' + path, data=body,
                         headers={'Content-Type': 'application/json'}), timeout=15) as response:
        return json.load(response)

try:
    assert request('/health/ready')['status'] == 'ready'
    product = request('/products')[0]
    order = request('/orders', {'customer_name': 'Workspace verification', 'product_id': product['id'], 'quantity': 2})
    assert order['total_cents'] == product['price_cents'] * 2
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        current = next(item for item in request('/orders') if item['id'] == order['id'])
        if current['status'] == 'fulfilled':
            print(f"PASS: order {order['id']} persisted and fulfilled through the gateway.")
            break
        time.sleep(1)
    else:
        raise RuntimeError('Order did not reach fulfilled within 30 seconds')
except Exception as exc:
    print(f'FAIL: {type(exc).__name__}: verification did not complete. Check service logs.', file=sys.stderr)
    raise SystemExit(1)
