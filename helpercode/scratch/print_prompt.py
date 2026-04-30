import os
import sys

# Manual .env loading
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k.strip('"').strip("'")] = v.strip('"').strip("'")

# Add local path to sys.path
sys.path.append('.')

# Now safe to import
from lseg_market_agent.agent import root_agent

print("Agent Name:", root_agent.name)
print("\n--- Agent Instructions ---")
print(root_agent.instruction)

print("\n--- Agent Tools ---")
# Wait, list of tools is created dynamically but we can list the components
print(root_agent.tools)
