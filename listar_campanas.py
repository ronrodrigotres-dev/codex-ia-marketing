from google.ads.googleads.client import GoogleAdsClient

# Cargar configuración desde google-ads.yaml
client = GoogleAdsClient.load_from_storage("C:/Users/LENOVO/miAsistenciaIA/google-ads.yaml")

# Reemplaza con tu ID de cliente (sin guiones)
customer_id = "1838759325"

ga_service = client.get_service("GoogleAdsService")

query = """
    SELECT campaign.id, campaign.name, campaign.status
    FROM campaign
    ORDER BY campaign.id
"""

response = ga_service.search(customer_id=customer_id, query=query)

for row in response:
    print(f"ID: {row.campaign.id}, Nombre: {row.campaign.name}, Estado: {row.campaign.status.name}")
