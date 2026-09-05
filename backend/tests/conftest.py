import pytest
from app.db.session import init_db, SessionLocal
from app.core.auth import seed_initial_admin

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initializes the SQLite schema and seeds the initial admin user for the test session."""
    init_db()
    db = SessionLocal()
    try:
        seed_initial_admin(db)
    finally:
        db.close()
