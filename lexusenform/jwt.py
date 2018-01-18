"""JWT Utilities"""

import base64
import json
import time
from typing import Dict

def token_is_expired(token: str) -> bool:
    """Check if JWT token is expired"""
    parsed = parse_jwt_claims(token)

    return time.time() > parsed['exp']

def parse_jwt_claims(token: str) -> Dict:
    """Parse the claims section from a JWT"""
    parts = token.split('.')

    if len(parts) != 3:
        raise ValueError("Token must be in JWT format. Missing header, claims, or sig.")

    return decode_base64json(parts[1])


def decode_base64json(data: str) -> Dict:
    """Decode base64'd JSON to a dictionary"""
    data += '=' * (-len(data) % 4)  # restore stripped '='s
    return json.loads(base64.b64decode(data).decode("utf-8"))
