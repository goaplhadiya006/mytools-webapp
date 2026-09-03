import os
import requests


RESEND_API_URL = "https://api.resend.com/emails"


def send_email(to_email, subject, html_content):
    api_key = os.environ.get("RESEND_API_KEY")

    if not api_key:
        print("ERROR: RESEND_API_KEY is not configured.")
        return False

    sender = os.environ.get(
        "MAIL_DEFAULT_SENDER",
        "onboarding@resend.dev"
    )

    try:
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": sender,
                "to": [to_email],
                "subject": subject,
                "html": html_content
            },
            timeout=30
        )

        if response.status_code in (200, 201):
            print("Email sent successfully.")
            return True

        print("Email sending failed:")
        print(response.status_code)
        print(response.text)
        return False

    except requests.RequestException as e:
        print("Email API error:", e)
        return False