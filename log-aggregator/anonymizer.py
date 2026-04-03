import hmac
import hashlib
import os

SALT = os.getenv("LOG_SALT", "default_salt").encode()

def anonymize_user_id(user_id: str) -> str:
    return hmac.new(SALT, user_id.encode(), hashlib.sha256).hexdigest()

def anonymize_ip(ip: str) -> str:
    return hmac.new(SALT, ip.encode(), hashlib.sha256).hexdigest()