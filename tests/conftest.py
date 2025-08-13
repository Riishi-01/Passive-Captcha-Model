import os
import sys
from pathlib import Path
import pytest


@pytest.fixture(scope="session", autouse=True)
def _ensure_backend_on_path():
    project_root = Path(__file__).resolve().parents[1]
    backend_path = project_root / "backend"
    sys.path.insert(0, str(backend_path))
    yield
    try:
        sys.path.remove(str(backend_path))
    except ValueError:
        pass


@pytest.fixture(scope="session")
def app():
    # Use isolated, fast settings for tests
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("SERVE_FRONTEND", "false")
    os.environ.setdefault("ENABLE_RATE_LIMITING", "false")
    os.environ.setdefault("ADMIN_SECRET", "testsecret")
    os.environ.setdefault("ALLOWED_ORIGINS", "*")
    # Explicit in-memory ratelimit backend to avoid warnings
    os.environ.setdefault("RATELIMIT_STORAGE_URI", "memory://")
    # Use in-memory SQLite for unit/integration tests
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

    # Create app using backend/main.py factory
    import main as backend_main
    flask_app, _socketio = backend_main.create_app('testing')
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


# Reduce noisy third-party warnings in tests
def pytest_configure(config):
    import warnings
    warnings.filterwarnings(
        "ignore",
        message=r"Using the in-memory storage for tracking rate limits.*",
        category=UserWarning,
        module=r"flask_limiter\.extension",
    )
    warnings.filterwarnings(
        "ignore",
        message=r"datetime\.datetime\.utcfromtimestamp\(\) is deprecated.*",
        category=DeprecationWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=r"datetime\.datetime\.utcnow\(\) is deprecated.*",
        category=DeprecationWarning,
    )


