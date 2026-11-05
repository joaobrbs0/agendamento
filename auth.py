"""Autoriza a conta Google uma vez e salva token.json.

Rode apenas uma vez (ou de novo se o token for revogado):
    python auth.py
"""
import os
from google_auth_oauthlib.flow import Flow

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # o redirect é http://localhost

SCOPES = ["https://www.googleapis.com/auth/calendar"]
REDIRECT = "http://localhost:8080/"

flow = Flow.from_client_secrets_file(
    "credentials.json", scopes=SCOPES, redirect_uri=REDIRECT
)
auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")

print("\n1) Abra este link no navegador e autorize:\n")
print(auth_url)
print("\n2) A página final vai dar erro de conexão. É normal.")
print("   Copie da barra de endereços a URL que começa com")
print("   http://localhost:8080/?state=...&code=... e cole abaixo.\n")

resposta = input("URL: ").strip()
flow.fetch_token(authorization_response=resposta)

with open("token.json", "w") as f:
    f.write(flow.credentials.to_json())

print("\ntoken.json salvo. Agora rode: python app.py")
