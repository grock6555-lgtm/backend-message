import secrets
import bcrypt
from typing import List

def generate_recovery_codes(count: int = 8, digits: int = 8) -> List[str]:
    return [''.join(secrets.choice('0123456789') for _ in range(digits)) for _ in range(count)]

def hash_recovery_codes(codes: List[str]) -> List[str]:
    return [bcrypt.hashpw(code.encode(), bcrypt.gensalt()).decode() for code in codes]

def verify_recovery_code(code: str, hashed: str) -> bool:
    return bcrypt.checkpw(code.encode(), hashed.encode())