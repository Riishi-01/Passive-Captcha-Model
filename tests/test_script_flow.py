import json
from uuid import uuid4


def test_script_collect_flow(app, client):
    # Seed a website row compatible with token manager fallbacks
    from app.database import get_db_session, Website
    from app.script_token_manager import init_script_token_manager
    import redis

    session = get_db_session()
    try:
        unique_domain = f'https://example-{uuid4().hex}.com'
        site = Website(
            id=f'site-{uuid4().hex}',
            domain=unique_domain,
            token=f'tok_{uuid4().hex[:8]}',
            name='Site 1'
        )
        session.add(site)
        session.commit()
    finally:
        session.close()

    # Initialize token manager with no redis (memory fallback)
    init_script_token_manager(None)

    # Generate a token via admin API requires auth; directly simulate script/collect with invalid token
    payload = {
        'website_url': unique_domain,
        'session_id': 'sess_123',
        'data': {
            'mouse': {'movementCount': 1, 'clickCount': 0, 'avgVelocity': 0.1, 'avgAcceleration': 0.0, 'entropy': 0.0},
            'keyboard': {'keystrokeCount': 0, 'avgTypingSpeed': 0.0, 'rhythm': 0.0},
            'scroll': {'scrollEventCount': 0, 'avgVelocity': 0.0, 'consistency': 0.0},
            'timing': {'pageLoadTime': 0, 'domReadyTime': 0, 'firstInteractionTime': 0, 'sessionDuration': 0},
            'device': {'screenResolution': {}, 'viewport': {}, 'colorDepth': 0, 'timezoneOffset': 0, 'touchSupport': False, 'deviceMemory': 0, 'hardwareConcurrency': 0, 'fonts': [], 'plugins': []}
        }
    }

    resp = client.post('/api/script/collect', json=payload, headers={'X-Script-Token': 'invalid'})
    assert resp.status_code in (400, 401, 503)


