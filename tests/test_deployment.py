from types import ModuleType


def test_wsgi_app_creation():
    import main as backend_main
    app = backend_main.get_wsgi_app()
    # Flask provides name attribute
    assert hasattr(app, 'route')


def test_production_app_routes():
    import os
    import main as backend_main

    os.environ.setdefault('SERVE_FRONTEND', 'false')
    os.environ.setdefault('ENABLE_RATE_LIMITING', 'false')
    os.environ.setdefault('ALLOWED_ORIGINS', '*')
    os.environ.setdefault('ADMIN_SECRET', 'prodtestsecret')
    os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

    app, _socketio = backend_main.create_app('production')
    rule_endpoints = {rule.rule for rule in app.url_map.iter_rules()}

    # Core health
    assert '/health' in rule_endpoints
    # Admin blueprint health
    assert '/admin/health' in rule_endpoints
    # Passive script serving
    assert '/passive-captcha-script.js' in rule_endpoints
    # Script API endpoints (url_prefix is baked into blueprint)
    assert any(p.startswith('/api/script') for p in rule_endpoints)


def test_healthcheck_ok():
    import os
    import main as backend_main

    os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
    app, _ = backend_main.create_app('production')
    client = app.test_client()
    resp = client.get('/health')
    assert resp.status_code == 200


