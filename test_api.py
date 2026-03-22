import requests, json
from app.utils.config import HUGGINGFACEHUB_API_TOKEN, HF_EMBEDDING_MODEL

url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{HF_EMBEDDING_MODEL}"
headers = {"Authorization": f"Bearer {HUGGINGFACEHUB_API_TOKEN}"}
res = requests.post(url, headers=headers, json={"inputs": ["test"]})
print(res.status_code)
print(res.text)
