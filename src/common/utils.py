from hashlib import sha256

import arrow


def get_local_isoformat(time: float, timezone: str) -> str:
    """Get localtime isoformat string from unix time"""
    return str(arrow.get(time).to(timezone).isoformat())


def generate_user_entry(username: str, password: str) -> str:
    """Generate user:password_hash line"""
    hasher = sha256()
    hasher.update(password.encode())
    password_hashed = hasher.hexdigest()
    return f"{username}:{password_hashed}"


def validate_password(password: str, password_hash: str) -> bool:
    """Check if the given password is correct"""
    hasher = sha256()
    hasher.update(password.encode())
    password_hashed = hasher.hexdigest()
    return password_hashed == password_hash
