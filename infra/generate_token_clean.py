from google_auth_oauthlib.flow import InstalledAppFlow

def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://www.googleapis.com/auth/adwords']
    )
    creds = flow.run_local_server(port=8080)
    print("\nTu REFRESH TOKEN es:\n")
    print(creds.refresh_token)

if __name__ == '__main__':
    main()
