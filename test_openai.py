from openai import OpenAI
from dotenv import load_dotenv
import os

# Carga el archivo .env
load_dotenv()

# Inicializa el cliente con la clave
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Prueba de conexión con una solicitud mínima
response = client.responses.create(
    model="gpt-4o-mini",
    input="Dime si la conexión con la API funciona correctamente."
)

# Imprime la respuesta
print(response.output[0].content[0].text)
