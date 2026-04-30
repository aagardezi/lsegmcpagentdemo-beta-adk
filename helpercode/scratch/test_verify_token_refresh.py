import os
import sys
import time
from unittest.mock import MagicMock

# Mocking modules that may be missing in local environment execution
sys.modules['google.genai'] = MagicMock()
sys.modules['google.genai.types'] = MagicMock()

# Add read-only ADK path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'read-only', 'adk-python', 'src'))

# Add bridge directory directly to avoid triggering lseg_market_agent.__init__
sys.path.insert(0, os.path.join(project_root, 'lseg_market_agent'))

import mcp_client_bridge


def test_caching():
    print("--- Test 1: First Call (should fetch) ---")
    token1 = mcp_client_bridge.get_lseg_token()
    print(f"Token 1 length: {len(token1)}")

    print("\n--- Test 2: Second Call (should use cache) ---")
    token2 = mcp_client_bridge.get_lseg_token()
    print(f"Token 2 length: {len(token2)}")
    assert token1 == token2, "Tokens should match"

    print("\n--- Test 3: Simulate Expiration ---")
    # Manually set expires_at in the past
    mcp_client_bridge._LSEG_TOKEN_CACHE["expires_at"] = time.time() - 100
    print("Set expires_at to past time.")

    print("\n--- Test 4: Third Call (should fetch again) ---")
    token3 = mcp_client_bridge.get_lseg_token()
    print(f"Token 3 length: {len(token3)}")

if __name__ == "__main__":
    test_caching()
