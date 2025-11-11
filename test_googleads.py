from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def main():
    try:
        client = GoogleAdsClient.load_from_storage("google-ads.yaml")
        print("✅ Conexión establecida con la API de Google Ads.")
    except GoogleAdsException as ex:
        print(f"❌ Error en la conexión: {ex}")
    except Exception as e:
        print(f"⚠️ Error general: {e}")

if __name__ == "__main__":
    main()
