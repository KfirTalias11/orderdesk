# HTTP API

All endpoints use the `/api` prefix through the gateway. The machine-readable OpenAPI schema is at `/api/openapi.json`. Interactive documentation requiring CDN assets is disabled.

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/products` | Catalog, sorted by ID |
| GET | `/orders` | Latest 200 orders, newest first |
| POST | `/orders` | Create a pending order and durable outbox entry |
| GET | `/status` | Dependencies, worker activity, all-time aggregates |
| GET | `/health/live` | Process liveness |
| GET | `/health/ready` | Dependency readiness; 200 or 503 |

Create an order:

```sh
curl http://localhost:8088/api/orders \
  -H 'Content-Type: application/json' \
  -d '{"customer_name":"Juniper Studio","product_id":1,"quantity":2}'
```

Customer names are trimmed, nonempty and at most 120 characters. Quantity is an integer between 1 and 1000. Unknown products return 404; invalid or extra fields return 422. The server computes total price in cents. Creation returns 201; database failures return 503 without connection credentials.

Orders include `id`, `customer_name`, `product_id`, `product_name`, `sku`, `quantity`, `total_cents`, `status`, `created_at`, and `fulfilled_at`. Status is `pending` or `fulfilled`; timestamps are UTC ISO 8601. Responses carry an `X-Request-ID` also present in request logs.

Creation currently has no client idempotency key. If a request times out after the server may have committed it, inspect the ledger before retrying. Fulfillment delivery itself is idempotent.
