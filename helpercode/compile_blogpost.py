import os
import markdown2

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bridging Institutional Data with Collaborative AI: The LSEG & Google ADK Market Intelligence Agent</title>
    <style>
        :root {{
            --color-primary: #039be5;
            --color-primary-light: #e1f5fe;
            --color-text: #2c3e50;
            --color-bg: #fcfcfc;
            --color-card-bg: #ffffff;
            --color-border: #e1e4e8;
            --color-code-bg: #f6f8fa;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: var(--color-text);
            background-color: var(--color-bg);
            margin: 0;
            padding: 0;
        }}

        .container {{
            max-width: 850px;
            margin: 40px auto;
            padding: 40px;
            background-color: var(--color-card-bg);
            border: 1px solid var(--color-border);
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }}

        h1, h2, h3, h4 {{
            font-weight: 600;
            color: #1a2530;
            margin-top: 24px;
            margin-bottom: 16px;
        }}

        h1 {{
            font-size: 2.2em;
            border-bottom: 1px solid var(--color-border);
            padding-bottom: 10px;
            margin-top: 0;
        }}

        h2 {{
            font-size: 1.6em;
            border-bottom: 1px solid var(--color-border);
            padding-bottom: 6px;
        }}

        p {{
            margin-top: 0;
            margin-bottom: 16px;
        }}

        a {{
            color: var(--color-primary);
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        ul, ol {{
            padding-left: 2em;
            margin-top: 0;
            margin-bottom: 16px;
        }}

        li {{
            margin-bottom: 6px;
        }}

        code {{
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 85%;
            background-color: var(--color-code-bg);
            padding: 0.2em 0.4em;
            border-radius: 3px;
        }}

        pre {{
            background-color: var(--color-code-bg);
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            border-radius: 6px;
            border: 1px solid var(--color-border);
        }}

        pre code {{
            background-color: transparent;
            padding: 0;
            font-size: inherit;
        }}

        table {{
            border-spacing: 0;
            border-collapse: collapse;
            width: 100%;
            margin-top: 0;
            margin-bottom: 16px;
        }}

        table th, table td {{
            padding: 6px 13px;
            border: 1px solid var(--color-border);
        }}

        table tr {{
            background-color: #fff;
            border-top: 1px solid #c6cbd1;
        }}

        table tr:nth-child(even) {{
            background-color: #f6f8fa;
        }}

        blockquote {{
            margin: 0 0 16px 0;
            padding: 0 1em;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
        }}

        img {{
            display: block;
            max-width: 100%;
            height: auto;
            margin: 24px auto;
            border: 1px solid var(--color-border);
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
        }}

        hr {{
            height: 0.25em;
            padding: 0;
            margin: 24px 0;
            background-color: var(--color-border);
            border: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
{content}
    </div>
</body>
</html>
"""

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    md_path = os.path.join(root_dir, "blogpost.md")
    html_path = os.path.join(root_dir, "blogpost.html")
    
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    
    # Render markdown to HTML using markdown2 with codehilite/fenced-code-blocks support
    html_content = markdown2.markdown(md_text, extras=["fenced-code-blocks", "tables"])
    
    full_html = HTML_TEMPLATE.format(content=html_content)
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)
        
    print(f"Successfully compiled {md_path} to {html_path}")

if __name__ == "__main__":
    main()
