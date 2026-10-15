# Configuration

| Variable | Used by | Default / contract |
| --- | --- | --- |
| `POSTGRES_PASSWORD` | Compose / PostgreSQL | Required; generated in ignored `.env` |
| `WEB_PORT` | Gateway host binding | `8088`, bound to `127.0.0.1` |
| `DATABASE_URL` | API, fulfillment | Compose supplies PostgreSQL service address |
| `REDIS_URL` | API, fulfillment | `redis://redis:6379/0` in Compose |
| `QUEUE_NAME` | Fulfillment | `orders:fulfillment` |
| `WORKER_POLL_SECONDS` | Fulfillment | `2`; valid range 0.1–5 seconds |
| `SERVICE_NAME` | Application logging | `orders-api` or `fulfillment` |

Generate `.env` using `python3 scripts/setup.py`. Use URL-safe credentials because Compose embeds the database password into a connection URI. The generator uses hexadecimal values. A changed password in `.env` does not rotate the password inside an existing database volume; perform a coordinated database credential rotation instead.

Compose environment values are deployment configuration; edit a local override to change service-specific variables. Recreate affected containers after configuration changes. A plain `docker compose restart` does not load a changed environment.

Database connections use a three-second connection timeout, five-second statement timeout and three-second lock timeout. Redis operations have two-second connection and socket timeouts. The worker retries on the next polling cycle. Outbox dispatch retries after ten seconds until completion.

Only the gateway publishes a port. Containers can resolve `api`, `db`, and `redis` on the application's Compose network. Service names are container-network addresses, not host DNS names.
