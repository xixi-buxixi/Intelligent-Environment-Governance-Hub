#!/usr/bin/env python3
import subprocess, json

# Login
r = subprocess.run(['curl','-s','-X','POST','https://www.lililiz.top/environment/api/auth/login',
    '-k','-H','Content-Type: application/json',
    '-d','{"username":"admin","password":"admin123"}'], capture_output=True, text=True)
token = json.loads(r.stdout)['data']['token']

# Check user info
r = subprocess.run(['curl','-s','https://www.lililiz.top/environment/api/auth/userinfo',
    '-k','-H',f'Authorization: Bearer {token}'], capture_output=True, text=True)
d = json.loads(r.stdout)
u = d.get('data', {})
print("=== Login User Info ===")
print(f"  realName: {u.get('realName')}")
print(f"  department: {u.get('department')}")
print(f"  role: {u.get('role')}")

# Check data sources
r = subprocess.run(['curl','-s','https://www.lililiz.top/environment/api/data/sources',
    '-k','-H',f'Authorization: Bearer {token}'], capture_output=True, text=True)
d = json.loads(r.stdout)
print("\n=== Data Sources ===")
for s in d.get('data', []):
    print(f"  {s['id']}: {s['sourceName']}")

# Check risk record 1
r = subprocess.run(['curl','-s','https://www.lililiz.top/environment/api/risk/records/1',
    '-k','-H',f'Authorization: Bearer {token}'], capture_output=True, text=True)
d = json.loads(r.stdout)
data = d.get('data', {})
print("\n=== Risk Record 1 ===")
print(f"  city: {data.get('city')}")
print(f"  riskLevel: {data.get('riskLevel')}")
exp = data.get('explanation', '')
print(f"  explanation length: {len(exp)}")
print(f"  explanation first 100: {exp[:100]}")
