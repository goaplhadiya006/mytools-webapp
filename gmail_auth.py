from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]


def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json",
        SCOPES
    )

    creds = flow.run_local_server(
        port=5000,
        access_type="offline",
        prompt="consent"
    )

    with open("token.json", "w") as token:
        token.write(creds.to_json())

    print("Gmail authorization successful!")
    print("token.json created.")


if __name__ == "__main__":
    main()