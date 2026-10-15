# OrderDesk

OrderDesk is a small order-management workspace for teams that need a clear view of customer orders and asynchronous fulfillment. Create orders from a product catalog, track their progress, and see the availability of the services that process them.

## Run locally

Requires Docker with Compose and Python 3. Initial builds download container images and Python packages.

```sh
python3 scripts/setup.py
docker compose up -d --build --wait
```

Open [localhost:8088](http://localhost:8088). The initial database includes six sample products and three fictional fulfilled orders. New orders are processed automatically.

The configuration generator creates an ignored `.env` with a random database password. It never replaces an existing file. Change `WEB_PORT` in `.env` if 8088 is occupied.

## Services

| Service | Responsibility | Dependencies |
| --- | --- | --- |
| Web gateway | Dashboard, HTTP entry point, API routing | Order API |
| Order API | Product lookup, validated order creation, order history | PostgreSQL; Redis for readiness |
| Fulfillment | Durable outbox dispatch and idempotent job processing | PostgreSQL, Redis |
| PostgreSQL | Catalog, orders, outbox, worker heartbeat | Persistent volume |
| Redis | Fulfillment job transport | Persistent volume |

The application services run as separate processes and containers and can be rebuilt or restarted independently. API and fulfillment currently share a database schema; see the [architecture](docs/architecture.md) for boundaries and tradeoffs.

## Verify

```sh
python3 scripts/smoke.py
# Dashboard regression checks (Node.js 22+)
node --test tests/web.test.cjs
# Isolated, disposable test dependencies; no production data is touched.
docker compose -p orderdesk-tests -f compose.test.yaml run --build --rm tests
docker compose -p orderdesk-tests -f compose.test.yaml down
```

The smoke check creates one real order named “Workspace verification” and waits for fulfillment. Integration tests cover validation, totals, persisted outbox entries, duplicate delivery, queue recovery, unavailable dependencies, and stale workers.

## Documentation

- [Architecture and data flow](docs/architecture.md)
- [Configuration](docs/configuration.md)
- [Operations and troubleshooting](docs/operations.md)
- [API contract](docs/api.md)

## Deployment scope

This version is a local single-operator workspace. There is no authentication or payment processing. The only published port binds to loopback; database and queue ports remain internal. Add authentication and TLS before exposing the gateway to a network. Runtime assets are bundled and require no external services. Kubernetes deployment manifests are not included yet.
