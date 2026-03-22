import json
import os

file_path = "/Users/sgardezi/work/projects/lsegmcpagentdemo-beta-adk/tools_list_response.txt"

if not os.path.exists(file_path):
    print(f"File not found at {file_path}")
    exit(1)

with open(file_path, 'r') as f:
    text = f.read()

# remove 'data: ' prefix if present (the grep output from before showed it)
if text.startswith("data: "):
    text = text[6:]

try:
    data = json.loads(text)
except json.JSONDecodeError as e:
    # Try cleaning up formatting, or finding the first {
    idx = text.find("{")
    if idx != -1:
         try:
              data = json.loads(text[idx:])
         except Exception as e2:
              print(f"Double parse fail: {e2}")
              exit(1)
    else:
         print(f"JSON parse error: {e}")
         exit(1)

tools = data.get("result", {}).get("tools", [])

print("# LSEG MCP Tools List\n")
print("| Tool Name | Title | Description Preview |")
print("|---|---|---|")

for tool in tools:
    name = tool.get("name")
    title = tool.get("title", "N/A")
    desc = tool.get("description", "").replace("\n", " ").strip()
    if len(desc) > 120:
         desc = desc[:117] + "..."
    print(f"| `{name}` | {title} | {desc} |")
