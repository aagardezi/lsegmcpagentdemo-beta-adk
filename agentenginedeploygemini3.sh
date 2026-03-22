#!/bin/bash

TARGET_URL="https://discoveryengine.googleapis.com/v1alpha/projects/genaillentsearch/locations/global/collections/default_collection/engines/as-fsi-uki-demo_1758301642647/assistants/default_assistant/agents" # 

JSON_DATA=$(cat <<EOF
{
    "displayName": "LSEG MCP Market Agent BETA - V6",
    "description": "Allows analysis of financial markets using LSEG MCP Gemini 3",
    "adk_agent_definition": 
    {
        "tool_settings": {
            "tool_description": "Various Market analysis tools via MCP"
        },
        "provisioned_reasoning_engine": {
            "reasoning_engine":"projects/884152252139/locations/us-central1/reasoningEngines/5260556758245441536"
        }
    }
}
EOF
)

echo "Sending POST request to: $TARGET_URL"
echo "Request Body:"
echo "$JSON_DATA"
echo ""

# Perform the POST request using curl
curl -X POST \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "X-Goog-User-Project: genaillentsearch" \
     -d "$JSON_DATA" \
     "$TARGET_URL"

echo "" # Add a newline after curl output for better readability
echo "cURL command finished."
