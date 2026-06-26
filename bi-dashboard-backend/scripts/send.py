import requests, json

with open(r'C:\Users\JunJun1\Desktop\社区数据测试api调用\社区数据.json', 'r', encoding='utf-8') as f:
    json_data = f.read()

url = 'https://power-api.yingdao.com/oapi/power/v1/rest/flow/a1237f50-0eff-4551-aa19-7802654d8c48/execute'
headers = {
    'Authorization': 'Bearer AP_WHyUK1D5ZsHpxBXH',
    'Content-Type': 'application/json; charset=utf-8'
}
payload = {'input': {'input_text_0': json_data}}

print('发送中...')
resp = requests.post(url, headers=headers, json=payload, timeout=60)
result = resp.json()

print('=== 响应结果 ===')
print(f"code: {result.get('code')}")
print(f"success: {result.get('success')}")
print(f"msg: {result.get('msg')}")
print(f"requestId: {result.get('requestId')}")
if result.get('data'):
    d = result['data']
    print(f"runRecordId: {d.get('runRecordId')}")
    r = d.get('result')
    if r:
        r_str = json.dumps(r, ensure_ascii=False)
        print(f"result (前500字符): {r_str[:500]}")
