import os
from google.cloud import secretmanager
from google.ads.googleads.client import GoogleAdsClient

def access_secret(project_id: str, secret_id: str) -> str:
    """Lee una versión del secreto desde Google Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8").strip()

def main():
    project_id = "ia-marketing-digita"

    # Leer secretos desde Secret Manager
    developer_token = access_secret(project_id, "ADS_DEVELOPER_TOKEN")
    client_id = access_secret(project_id, "ADS_CLIENT_ID")
    client_secret = access_secret(project_id, "ADS_CLIENT_SECRET")
    refresh_token = access_secret(project_id, "ADS_REFRESH_TOKEN")

    # Crear archivo temporal google-ads.yaml
    config_yaml = f"""
developer_token: "{developer_token}"
client_id: "{client_id}"
client_secret: "{client_secret}"
refresh_token: "{refresh_token}"
login_customer_id: "1838759325"
use_proto_plus: True
"""
    with open("google-ads-temp.yaml", "w") as f:
        f.write(config_yaml)

    # Inicializar cliente de Google Ads
    client = GoogleAdsClient.load_from_storage("google-ads-temp.yaml")

    # Consulta GAQL de prueba
    query = """
    SELECT
      customer.id,
      customer.descriptive_name
    FROM customer
    LIMIT 1
    """

    ga_service = client.get_service("GoogleAdsService")
    response = ga_service.search(customer_id="1838759325", query=query)

    for row in response:
        print(f"✅ Conexión exitosa: {row.customer.descriptive_name}")

if __name__ == "__main__":
    main()
