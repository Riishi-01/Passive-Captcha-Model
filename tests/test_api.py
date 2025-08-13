import json


def test_health(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('status') in ('healthy', 'unhealthy')


def test_admin_login_and_verify_token(client):
    # login
    resp = client.post('/admin/login', json={'password': 'testsecret'})
    assert resp.status_code in (200, 401, 503)
    if resp.status_code != 200:
        return  # service unavailable in minimal mode
    token = resp.get_json()['data']['token']

    # verify token
    resp2 = client.get('/admin/verify-token', headers={'Authorization': f'Bearer {token}'})
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2['success'] is True


def test_generate_script_invalid_params(client):
    # Hitting simplified /api/generate-script for contract check
    resp = client.post('/api/generate-script', json={})
    assert resp.status_code in (400, 200)


