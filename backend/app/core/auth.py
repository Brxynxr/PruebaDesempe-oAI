from datetime import datetime, timezone, timedelta
from typing import Optional
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_db
from app.db.models import AdminUser

security_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials: token invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_admin_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> AdminUser:
    """Dependency that extracts and validates the Admin user from the Bearer JWT token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided in 'Authorization: Bearer <token>' header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(AdminUser).where(AdminUser.username == username)
    user = db.scalars(stmt).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La cuenta de usuario no existe o se encuentra desactivada.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def require_admin_role(
    current_user: AdminUser = Depends(get_current_admin_user)
) -> AdminUser:
    """Dependency that enforces superadmin permissions."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requieren permisos de Administrador para esta acción."
        )
    return current_user

def seed_initial_admin(db: Session) -> None:
    """Ensures at least the default admin account from environment variables exists in the database with role 'admin'."""
    admin_user = settings.ADMIN_USERNAME
    admin_pass = settings.ADMIN_PASSWORD
    if not admin_user or not admin_pass:
        return

    stmt = select(AdminUser).where(AdminUser.username == admin_user)
    existing = db.scalars(stmt).first()
    if not existing:
        hashed = hash_password(admin_pass)
        new_admin = AdminUser(
            username=admin_user, 
            password_hash=hashed,
            full_name="Administrador Principal",
            role="admin",
            is_active=True
        )
        db.add(new_admin)
        db.commit()
    else:
        # Ensure initial admin has 'admin' role and is active
        updated = False
        if existing.role != "admin":
            existing.role = "admin"
            updated = True
        if not existing.is_active:
            existing.is_active = True
            updated = True
        if not verify_password(admin_pass, existing.password_hash):
            existing.password_hash = hash_password(admin_pass)
            updated = True
        if updated:
            db.commit()
