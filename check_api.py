import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
url = "https://api.openai.com/v1/chat/completions"

data = {
    "model": "gpt-4o-mini",
    "messages": [
        {"role": "user", "content": "Hola, ¿cómo estás?"}
    ]
}

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
    print("✅ Conexión exitosa")
    print("Respuesta:", response.json()["choices"][0]["message"]["content"])
else:
    print(f"❌ Error {response.status_code}: {response.text}")
