from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    r"C:\Users\LENOVO\miAsistenciaIA\client_secret_2_819648047297-65qmhrm1pg5nlf4pmc6gmqs25nf5ab.apps.googleusercontent.com.json",
    scopes=["https://www.googleapis.com/auth/adwords"]
)

creds = flow.run_local_server(port=0)
print("\nREFRESH TOKEN:")
print(creds.refresh_token)
