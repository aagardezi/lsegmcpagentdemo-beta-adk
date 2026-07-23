import base64
import requests
import os

mermaid_code = """graph TD
    User([User Prompt]) --> Orchestrator[Root Orchestrator]
    Orchestrator -->|1. Search & Fetch| LSEG[LSEG MCP Server]
    LSEG -->|2. Data Return| Orchestrator
    Orchestrator -->|3. Proactive Delegate| Graphing[Python Graphing Agent]
    Orchestrator -->|3. Or Bypass if no numeric trend| RiskCritique[Risk Auditor Agent]
    Graphing -->|4. Plot Data & Transfer| RiskCritique
    RiskCritique -->|5. Audit & Transfer| Report[Report Writer Agent]
    Report -->|6. Compile Report & Transfer| PDFGen[PDF Generator Agent]
    PDFGen -->|7. Generate PDF| UserResponse([Final Response / PDF Artifact])"""

def main():
    # Base64 encode the mermaid code
    # mermaid.ink requires standard base64 encoding (not urlsafe, or sometimes urlsafe is supported, let's use standard b64)
    # Let's clean up line endings to ensure they are standard
    clean_code = "\n".join([line.rstrip() for line in mermaid_code.splitlines()])
    encoded_bytes = base64.b64encode(clean_code.encode('utf-8'))
    encoded_string = encoded_bytes.decode('utf-8')
    
    url = f"https://mermaid.ink/img/{encoded_string}"
    print(f"Requesting Mermaid rendering from: {url}")
    
    # Optional parameters (theme=default, bgColor=white)
    # Since we want a high-res image with white background:
    response = requests.get(url + "?bgColor=white")
    if response.status_code == 200:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_path = os.path.join(root_dir, "images", "pipeline_flowchart_blog2.png")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"Successfully saved Mermaid diagram to: {output_path}")
    else:
        print(f"Error fetching Mermaid diagram: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
