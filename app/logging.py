import json
import os
from datetime import datetime, timezone


def event(name, **fields):
    print(json.dumps({'timestamp': datetime.now(timezone.utc).isoformat(),
                      'service': os.getenv('SERVICE_NAME', 'orders-api'),
                      'event': name, **fields}), flush=True)
