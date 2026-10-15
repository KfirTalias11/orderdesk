import os
import psycopg
from psycopg.rows import dict_row
from redis import Redis


def connection():
    return psycopg.connect(os.environ['DATABASE_URL'], row_factory=dict_row, connect_timeout=3,
                           options='-c statement_timeout=5000 -c lock_timeout=3000')


def queue():
    return Redis.from_url(os.environ['REDIS_URL'], decode_responses=True,
                          socket_connect_timeout=2, socket_timeout=2)


def queue_name():
    return os.getenv('QUEUE_NAME', 'orders:fulfillment')
