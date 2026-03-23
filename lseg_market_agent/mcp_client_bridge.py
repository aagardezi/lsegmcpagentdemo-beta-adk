import os
import time
import requests
from typing import Dict
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.agents.readonly_context import ReadonlyContext

# Token cache with absolute expiration time
_LSEG_TOKEN_CACHE = {
    "access_token": None,
    "expires_at": 0.0
}

def get_lseg_token() -> str:
    """Fetches the LSEG Authorization JWT using client-credentials."""
    global _LSEG_TOKEN_CACHE
    
    current_time = time.time()
    # Check if cached token is still valid (adding a 60-second buffer)
    if _LSEG_TOKEN_CACHE["access_token"] and current_time + 60 < _LSEG_TOKEN_CACHE["expires_at"]:
        print("Using cached LSEG access token...")
        return _LSEG_TOKEN_CACHE["access_token"]
        
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
    
    res_json = response.json()
    token = res_json.get("access_token")
    expires_in = res_json.get("expires_in", 7200) # Default to 2 hours if not provided
    
    if not token:
        raise ValueError("Failed to retrieve access token from LSEG")
        
    # Update cache
    _LSEG_TOKEN_CACHE["access_token"] = token
    _LSEG_TOKEN_CACHE["expires_at"] = current_time + expires_in
    
    print(f"Token refreshed successfully. Expires in {expires_in} seconds.")
    return token

def lseg_header_provider(context: ReadonlyContext) -> Dict[str, str]:
    """Provides dynamic Authorization header for MCP sessions."""
    token = get_lseg_token()
    return {"Authorization": f"Bearer {token}"}

def create_lseg_mcp_toolset() -> MCPToolset:
    """Creates the ADK MCPToolset authenticated to LSEG's API."""
    # Fetch initial token for discovery
    token = get_lseg_token()
    
    return MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url="https://api.analytics.lseg.com/lfa/mcp",
            headers={
                "Authorization": f"Bearer {token}",
            },
            timeout=180.0  # 3 minutes for long-running quantitative requests
        ),
        header_provider=lseg_header_provider
    )

