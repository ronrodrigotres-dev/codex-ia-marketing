from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    r"C:\Users\LENOVO\miAsistenciaIA\client_secret_2_819648047297-65qmhrm1pg5nlf1k4pmc6gmqs25nf5ab.apps.googleusercontent.com.json",
    scopes=["https://www.googleapis.com/auth/adwords"]
)
creds = flow.run_local_server(port=8080)
print("Refresh token generado:")
print(creds.refresh_token)
