# Operations

## Start, inspect, stop

```sh
docker compose up -d --build --wait
docker compose ps
docker compose logs --since 5m api worker web
python3 scripts/smoke.py
docker compose down
```

`down` preserves named data volumes. Do not add `--volumes` unless you intend to erase orders. Build and deploy an individual application service with `docker compose up -d --build --no-deps api` (or `worker`, `web`). Shared image changes require recreating both API and worker when both need the new version.

## Troubleshooting

| Symptom | Inspect | Recovery |
| --- | --- | --- |
| Dashboard unreachable | Gateway state, host port conflicts | Start web; select a free `WEB_PORT` and recreate web |
| Gateway returns 502 | API container state and gateway logs | Restore API; Docker DNS is re-resolved every five seconds |
| API returns 503 | Readiness result, database logs and address | Restore connectivity/configuration, recreate changed services |
| Orders stay pending | Worker logs, heartbeat, Redis and outbox | Restore worker/Redis; unfinished jobs retry automatically |
| Worker restarts repeatedly | Poll interval, environment, logs | Correct invalid configuration and recreate worker |
| Existing database lacks new fields | Applied schema versus application version | Apply reviewed migration or restore compatible app version |

API and worker logs are JSON lines. `order.created`, `job.dispatched`, and `order.fulfilled` connect activity through `order_id`. `dependency.failed` and `worker.retry` report safe exception types. The database is authoritative if Redis loses transport messages. A running worker heartbeat alone does not prove successful fulfillment.

Docker health checks report health but do not automatically restart an unhealthy running process. Restart policies act on process exits. Log rotation is bounded to three 10 MB files per service.

## Backups

```sh
mkdir -p .local/backups
docker compose exec -T db pg_dump -U orderdesk -d orderdesk > .local/backups/orders.sql
```

Backups may contain customer data. Keep them private. Test restoration into a separate database before using a backup for recovery; restoring over a live database is not part of normal startup.

## Offline deployment

On a connected machine of the same CPU architecture, build and export images:

```sh
docker compose build
docker image save orderdesk-app:local orderdesk-web:local postgres:16-alpine redis:7-alpine -o orderdesk-images.tar
```

Transfer the image archive and application checkout using your approved process. On the destination, load the archive, generate `.env`, and run without rebuilding or pulling:

```sh
docker image load -i orderdesk-images.tar
python3 scripts/setup.py
docker compose up -d --no-build --pull never --wait
```

Images contain all runtime dependencies and web assets. The initial SQL directory must accompany the checkout. Test images and Python tooling are separate from runtime deployment. Deployment uses version tags; record image digests when promoting an exact release.
