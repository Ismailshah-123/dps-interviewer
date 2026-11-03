async def test_health(client):
    r=await client.get('/api/v1/health/live')
    assert r.status_code == 200
    assert r.json()['status']=='alive'

async def test_login_and_create_candidate(client):
    r=await client.post('/api/v1/auth/login', json={'email':'admin@dps.example.com','password':'TestPassword123!'})
    assert r.status_code == 200, r.text
    token=r.json()['access_token']
    headers={'Authorization':f'Bearer {token}'}
    r=await client.post('/api/v1/candidates', headers=headers, json={'name':'Synthetic Candidate','grade':'Grade 5','metadata':{}})
    assert r.status_code == 201, r.text
    assert r.json()['reference_number'].startswith('DPS-')
