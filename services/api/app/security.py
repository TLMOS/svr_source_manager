import bcrypt


def get_password_hash(password: str) -> str:
    """Get password hash."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password."""
    return bcrypt.checkpw(password.encode(), password_hash.encode())
