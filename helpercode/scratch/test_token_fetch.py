import os
import requests
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("LSEG_CLIENT_ID")
client_secret = os.getenv("LSEG_CLIENT_SECRET")

url = "https://login.ciam.refinitiv.com/as/token.oauth2"
headers = {"Content-Type": "application/x-www-form-urlencoded"}
data = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": "lfa"
}

response = requests.post(url, headers=headers, data=data)
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
