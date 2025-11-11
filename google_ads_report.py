from google.ads.googleads.client import GoogleAdsClient

# Cargar configuración desde google-ads.yaml
client = GoogleAdsClient.load_from_storage("google-ads.yaml")

# Reemplaza con tu ID de cliente real (sin guiones)
customer_id = "1234567890"

# Consulta GAQL
query = """
SELECT
  campaign.name,
  metrics.clicks,
  metrics.impressions,
  metrics.ctr,
  metrics.average_cpc,
  metrics.conversions
FROM campaign
WHERE segments.date DURING LAST_7_DAYS
"""

# Ejecutar la consulta
ga_service = client.get_service("GoogleAdsService")
response = ga_service.search_stream(customer_id=customer_id, query=query)

# Mostrar resultados
for batch in response:
    for row in batch.results:
        print(
            f"Campaña: {row.campaign.name}, "
            f"Clicks: {row.metrics.clicks}, "
            f"Impresiones: {row.metrics.impressions}, "
            f"CTR: {row.metrics.ctr:.2%}, "
            f"CPC Promedio: {row.metrics.average_cpc.micros/1e6:.2f} USD, "
            f"Conversiones: {row.metrics.conversions}"
        )
