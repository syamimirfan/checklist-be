"""Random secrets handed to the client (refresh tokens, emailed links).

The database only ever stores the SHA-256 digest of a secret, so a leaked table can't be replayed.
A fast hash is enough here because the secrets are long and random, unlike passwords.
"""

import hashlib
import secrets


def generate_opaque_token():
    return secrets.token_urlsafe(32)


def hash_opaque_token(token):
    return hashlib.sha256(token.encode()).hexdigest()
