import os
import signal
import threading
from app.db import connection, queue, queue_name
from app.logging import event

stop = threading.Event()


def heartbeat():
    with connection() as db:
        db.execute("INSERT INTO worker_status(name,heartbeat_at) VALUES ('fulfillment',now()) ON CONFLICT(name) DO UPDATE SET heartbeat_at=now()")


def dispatch_pending():
    with connection() as db:
        rows = db.execute("""SELECT order_id FROM outbox WHERE completed_at IS NULL
            AND (dispatched_at IS NULL OR dispatched_at < now()-interval '10 seconds')
            ORDER BY order_id LIMIT 50 FOR UPDATE SKIP LOCKED""").fetchall()
        broker = queue()
        for row in rows:
            broker.rpush(queue_name(), row['order_id'])
            db.execute('UPDATE outbox SET dispatched_at=now() WHERE order_id=%s', (row['order_id'],))
            event('job.dispatched', order_id=row['order_id'], queue=queue_name())


def fulfill_order(order_id):
    with connection() as db:
        # Lock outbox first, matching dispatcher lock order.
        job = db.execute('SELECT * FROM outbox WHERE order_id=%s FOR UPDATE', (order_id,)).fetchone()
        if not job or job['completed_at'] is not None:
            return False
        result = db.execute("UPDATE orders SET status='fulfilled',fulfilled_at=now() WHERE id=%s AND status='pending' RETURNING id", (order_id,)).fetchone()
        db.execute('UPDATE outbox SET completed_at=now() WHERE order_id=%s', (order_id,))
        db.execute("INSERT INTO worker_status(name,heartbeat_at,last_success_at) VALUES ('fulfillment',now(),now()) ON CONFLICT(name) DO UPDATE SET last_success_at=now(),heartbeat_at=now()")
    if result:
        event('order.fulfilled', order_id=order_id)
    return bool(result)


def main():
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    interval = float(os.getenv('WORKER_POLL_SECONDS', '2'))
    if not 0.1 <= interval <= 5:
        raise ValueError('WORKER_POLL_SECONDS must be between 0.1 and 5')
    event('worker.started', queue=queue_name())
    while not stop.is_set():
        try:
            heartbeat()
            dispatch_pending()
            for _ in range(50):
                item = queue().lpop(queue_name())
                if item is None or stop.is_set():
                    break
                try:
                    fulfill_order(int(item))
                except ValueError:
                    event('job.invalid', reason='non_integer_order_id')
        except Exception as exc:
            event('worker.retry', error_type=type(exc).__name__)
        stop.wait(interval)
    event('worker.stopped')


if __name__ == '__main__':
    main()
