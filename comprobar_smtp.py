import msal
import requests
import os

from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REMITENTE = os.getenv("REMITENTE")
DESTINATARIO = os.getenv("DESTINATARIO")  # pon tu correo para la prueba
NOMBRE_DESTINATARIO = os.getenv("NOMBRE_DESTINATARIO")  # pon tu nombre para la prueba

# Obtener token
app = msal.ConfidentialClientApplication(
    client_id=CLIENT_ID,
    client_credential=CLIENT_SECRET,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}"
)
result = app.acquire_token_for_client(["https://graph.microsoft.com/.default"])

if "access_token" not in result:
    print("Error al obtener token:", result.get("error_description"))
else:
    print("Token obtenido OK")

    payload = {
        "message": {
            "subject": f"CFDI LOGYM - {NOMBRE_DESTINATARIO}",
            "body": {"contentType": "Text", "content": "Correo de nominas desde la app."},
            "toRecipients": [{"emailAddress": {"address": DESTINATARIO, "name": NOMBRE_DESTINATARIO}}]
        }
    }
    headers = {
        "Authorization": f"Bearer {result['access_token']}",
        "Content-Type": "application/json"
    }
    r = requests.post(
        f"https://graph.microsoft.com/v1.0/users/{REMITENTE}/sendMail",
        headers=headers,
        json=payload
    )
    if r.status_code == 202:
        print("Correo enviado OK")
    else:
        print(f"Error {r.status_code}:", r.text)