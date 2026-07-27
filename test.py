import os
import requests

url = "https://api.siliconflow.cn/v1/rerank"
headers = {
    "Authorization": f"Bearer {os.environ.get('SILICONFLOW_API_KEY')}",
    "Content-Type": "application/json",
}
payload = {
    "model": "Qwen/Qwen3-Reranker-8B",
    "query": "Apple",
    "documents": ["apple", "banana", "fruit", "vegetable"],
    "return_documents": True,
    "top_n": 4,
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
