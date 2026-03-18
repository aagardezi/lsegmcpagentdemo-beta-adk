import os
import requests
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

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

def create_lseg_mcp_toolset() -> MCPToolset:
    """Creates the ADK MCPToolset authenticated to LSEG's API."""
    token = get_lseg_token()
    
    return MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url="https://api.analytics.lseg.com/lfa/mcp",
            headers={
                "Authorization": f"Bearer {token}",
                # The server expects either SSE headers to initiate a session or JSON for commands
                # We do not override Accept here; the ADK SseConnectionParams / mcp python SDK will handle SSE initiation correctly.
            },
            timeout=180.0  # 3 minutes for long-running quantitative requests
        )
    )
