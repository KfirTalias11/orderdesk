"""Create local configuration without overwriting existing credentials."""
import os
import secrets
from pathlib import Path

root = Path(__file__).resolve().parent.parent
try:
    fd = os.open(root / '.env', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    print('Existing .env preserved.')
else:
    with os.fdopen(fd, 'w') as config:
        config.write(f'POSTGRES_PASSWORD={secrets.token_hex(24)}\nWEB_PORT=8088\n')
    print('Created .env with a generated database password.')
