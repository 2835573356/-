import requests, json
r = requests.get('http://localhost:8000/api/v1/posts', params={'page_size': 3}, timeout=5)
data = r.json()
print('Status:', r.status_code)
if data.get('success'):
    d = data['data']
    print(f'Total posts: {d.get("total", 0)}')
    for p in d.get('items', [])[:3]:
        print(f'  [{p["category"]}] {p["title"][:60]}')

r = requests.get('http://localhost:8000/api/v1/dashboard/summary', timeout=5)
print('\nDashboard:', r.status_code, json.dumps(r.json(), ensure_ascii=False, indent=2)[:400])
