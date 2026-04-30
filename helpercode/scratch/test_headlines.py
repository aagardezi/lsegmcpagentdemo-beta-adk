import os

import requests


def get_lseg_token() -> str:
    """Fetches the LSEG Authorization JWT using client-credentials."""
    client_id = os.getenv("LSEG_CLIENT_ID")
    client_secret = os.getenv("LSEG_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("LSEG_CLIENT_ID and LSEG_CLIENT_SECRET must be set in the environment.")

    url = "https://login.ciam.refinitiv.com/as/token.oauth2"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "lfa"
    }

    print("Fetching new LSEG access token...")
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()

    token = response.json().get("access_token")
    if not token:
        raise ValueError("Failed to retrieve access token from LSEG")

    return token

# Load environment variables from .env
from dotenv import load_dotenv

load_dotenv()

try:
    token = get_lseg_token()
except Exception as e:
    print(f"Error getting token: {e}")
    import sys
    sys.exit(1)

url = "https://api.analytics.lseg.com/lfa/mcp"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}

def call_tool(arguments, label):
    print(f"\n--- Testing {label} ---")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "insight_headlines",
            "arguments": arguments
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        print(f"Status Code: {response.status_code}")
        print("Response Content (Lines):")
        found_data = False
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                print(decoded_line)
                if '"content"' in decoded_line:
                    found_data = True
        return found_data
    except Exception as e:
        print(f"Error making request: {e}")
        return False

# Test 1: VOD.L in rics
call_tool({"rics": "VOD.L"}, "RICS: VOD.L")

# Test 2: Vodafone in query
call_tool({"query": "Vodafone"}, "Query: Vodafone")

# Test 3: AAPL.O in rics (Verify if headlines work general)
call_tool({"rics": "AAPL.O"}, "RICS: AAPL.O")

# Test 4: Topic search (B:278 example from description)
call_tool({"topics": "B:278"}, "Topics: B:278")
