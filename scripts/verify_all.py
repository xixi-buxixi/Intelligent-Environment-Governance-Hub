#!/usr/bin/env python3
import subprocess, json

def api(path, method='GET', token='', data=None):
    headers = ['-H', 'Content-Type: application/json']
    if token:
        headers += ['-H', f'Authorization: Bearer {token}']
    cmd = ['curl', '-s', '--max-time', '10', '-X', method, f'http://localhost:8083/environment/api{path}'] + headers
    if data:
        cmd += ['-d', json.dumps(data)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(r.stdout)

# Login
login = api('/auth/login', 'POST', data={'username': 'admin', 'password': 'admin123'})
token = login['data']['token']
print(f'Token: {token[:30]}...')
print()

# User list
print('=== User List ===')
r = api('/system/user/list?pageNum=1&pageSize=5', token=token)
print(f'code: {r.get("code")}')
if r.get('code') == 200:
    for u in r['data']['records']:
        print(f"  {u['id']}: {u['realName']} / {u['department']} / {u['role']}")
else:
    print(f'message: {r.get("message", "")}')
print()

# Data sources
print('=== Data Sources ===')
r = api('/data/sources', token=token)
print(f'code: {r.get("code")}')
data_list = r.get('data') if isinstance(r.get('data'), list) else []
for s in data_list[:5]:
    print(f"  {s['id']}: {s['sourceName']}")
print()

# Risk records
print('=== Risk Records ===')
r = api('/risk/records?pageNum=1&pageSize=3', token=token)
print(f'code: {r.get("code")}')
if r.get('code') == 200:
    for rec in r['data']['records'][:3]:
        exp = (rec.get('explanation', '') or '')[:80]
        print(f"  id={rec['id']} city={rec['city']} level={rec['riskLevel']} explain={exp}")
print()

# Python health
r = subprocess.run(['curl', '-s', '--max-time', '5', 'http://localhost:5001/health'], capture_output=True, text=True)
print(f'Python Health: {r.stdout.strip()}')
