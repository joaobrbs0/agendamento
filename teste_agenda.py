import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # o redirect é http://localhost

SCOPES = ["https://www.googleapis.com/auth/calendar"]
REDIRECT = "http://localhost:8080/"

flow = Flow.from_client_secrets_file(
    "credentials.json", scopes=SCOPES, redirect_uri=REDIRECT
)
auth_url, _ = flow.authorization_url(prompt="consent")

print("\n1) Abra este link no navegador e autorize:\n")
print(auth_url)
print("\n2) A página final vai dar erro de conexão. É normal.")
print("   Copie a URL COMPLETA da barra de endereços e cole abaixo.\n")

resposta = input("URL: ").strip()
flow.fetch_token(authorization_response=resposta)

service = build("calendar", "v3", credentials=flow.credentials)

evento = service.events().insert(
    calendarId="primary",
    body={
        "summary": "Teste de integração",
        "start": {"dateTime": "2026-11-05T14:00:00-03:00", "timeZone": "America/Sao_Paulo"},
        "end":   {"dateTime": "2026-11-05T14:30:00-03:00", "timeZone": "America/Sao_Paulo"},
        "attendees": [{"email": "joaovictorbrbs0@gmail.com"}],
    },
    sendUpdates="all",
).execute()

print("\nEvento criado:", evento["htmlLink"])