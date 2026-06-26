import requests, json

file_path = r'C:\Users\JunJun1\Desktop\社区数据测试api调用\社区数据.xlsx'
UPLOAD_URL = 'https://power-api.yingdao.com/oapi/power/v1/file/upload'
API_URL = 'https://power-api.yingdao.com/oapi/power/v1/rest/flow/4b8eb5ba-1ebb-4173-8023-f80511d2dd18/execute'
headers_auth = {'Authorization': 'Bearer AP_WHyUK1D5ZsHpxBXH'}

# Step 1: 上传文件
print('Step 1: 上传文件...')
with open(file_path, 'rb') as f:
    files = {'file': f}
    resp = requests.post(UPLOAD_URL, headers=headers_auth, files=files)
    upload_result = resp.json()
    print(f'上传响应: {json.dumps(upload_result, ensure_ascii=False, indent=2)}')

# Step 2: 用上传结果调用工作流
print('\nStep 2: 调用工作流...')
headers_json = {**headers_auth, 'Content-Type': 'application/json; charset=utf-8'}

# 上传返回: {"data": {"fileReadUrl": "https://..."}, "code": 200, "success": true}
import os
data = upload_result.get('data', upload_result)
url = data.get('fileReadUrl', '')
filename = os.path.basename(file_path)

payload = {
    'input': {
        'uploaded_file': {
            'filename': filename,
            'url': url
        }
    }
}
print(f'请求体: {json.dumps(payload, ensure_ascii=False, indent=2)[:500]}')

resp2 = requests.post(API_URL, headers=headers_json, json=payload, timeout=60)
result = resp2.json()

print(f'\n=== 工作流响应 ===')
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
        print(f"result (前1000字符):\n{r_str[:1000]}")
