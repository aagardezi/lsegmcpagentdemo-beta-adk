import os
import re
import sys
import markdown2
from fpdf import FPDF

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unlocking LSEG Data: Build Custom Financial Agents in Gemini Enterprise with LSEG MCP</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: #2c3e50;
            background-color: #ffffff;
            margin: 0;
            padding: 40px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background-color: #ffffff;
        }

        h1, h2, h3, h4 {
            font-weight: 600;
            color: #1a2530;
            margin-top: 28px;
            margin-bottom: 16px;
        }

        h1 {
            font-size: 2.2em;
            border-bottom: 2px solid #eaecef;
            padding-bottom: 12px;
            margin-top: 0;
        }

        h2 {
            font-size: 1.6em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 8px;
        }

        p {
            margin-top: 0;
            margin-bottom: 16px;
        }

        a {
            color: #0377bc;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        ul, ol {
            padding-left: 2em;
            margin-top: 0;
            margin-bottom: 16px;
        }

        li {
            margin-bottom: 8px;
        }

        code {
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 85%;
            background-color: #f6f8fa;
            padding: 0.2em 0.4em;
            border-radius: 3px;
        }

        pre {
            background-color: #f6f8fa;
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            border-radius: 6px;
            border: 1px solid #eaecef;
        }

        pre code {
            background-color: transparent;
            padding: 0;
            font-size: inherit;
        }

        table {
            border-spacing: 0;
            border-collapse: collapse;
            width: 100%;
            margin-top: 0;
            margin-bottom: 16px;
        }

        table th, table td {
            padding: 8px 13px;
            border: 1px solid #eaecef;
        }

        table tr {
            background-color: #fff;
            border-top: 1px solid #c6cbd1;
        }

        table tr:nth-child(even) {
            background-color: #f6f8fa;
        }

        blockquote {
            margin: 0 0 16px 0;
            padding: 0 1em;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
        }

        img {
            display: block;
            max-width: 100%;
            height: auto;
            margin: 24px auto;
            border: 1px solid #eaecef;
            border-radius: 6px;
        }

        hr {
            height: 0.25em;
            padding: 0;
            margin: 24px 0;
            background-color: #eaecef;
            border: 0;
        }
    </style>
</head>
<body>
    <div class="container">
{content}
    </div>
</body>
</html>
"""

class ReportPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 10)
        self.cell(0, 10, 'LSEG & Google Cloud Market Intelligence Blog', border=False, align='C')
        self.ln(10)
        self.line(10, 18, 200, 18) # Draw line under header
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

def clean_text_for_pdf(text: str) -> str:
    """Replaces Unicode symbols that are unsupported by basic PDF fonts."""
    replacements = {
        '\u2013': '-', '\u2014': '-', '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"', '\u2026': '...',
        '\u20ac': 'EUR ', '\u00a3': 'GBP ', '\u00a5': 'JPY ',
        '•': '-', '™': '(TM)', '©': '(C)', '®': '(R)',
        '✓': '[x]', 'Δ': 'Delta', '⚡': 'Power:', '🏗️': 'Architecture:',
        '🔌': 'Integration:', '💡': 'Benefits:', '🛡️': 'Security:',
        '🔗': 'Connection:', '🚀': 'Deploy:', '🧪': 'Testing:',
        '🔮': 'Outlook:', '📈': 'Chart:', '📊': 'Visualization:',
        '👉': '->', '✔️': '[x]', '⭐': '*', '🔥': 'Highlight:',
        '🤖': 'Agent:', '☕': 'Java:', '💼': 'Business:',
        '🌐': 'Web:', '💾': 'Save:', '📝': 'Note:', '🔍': 'Search:'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    # Strip remaining emojis/unsupported chars
    cleaned = []
    for char in text:
        try:
            char.encode('latin-1')
            cleaned.append(char)
        except UnicodeEncodeError:
            cleaned.append('?')
    return "".join(cleaned)

def md_to_pdf(md_text: str, output_pdf_path: str):
    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font('helvetica', '', 10)

    # Clean text to prevent PDF font failures
    md_text = clean_text_for_pdf(md_text)

    # Split the markdown text into parts so we can render images inline
    # markdown2/fpdf2 write_html doesn't reliably handle local img layout with text wrapper,
    # so we parse the markdown blocks, render text via write_html, and append images cleanly using FPDF's native image method.
    blocks = re.split(r'(!\[.*?\]\(.*?\))', md_text)

    for block in blocks:
        if not block.strip():
            continue
        
        # Check if block is an image tag
        img_match = re.match(r'!\[.*?\]\((.*?)\)', block)
        if img_match:
            img_path = img_match.group(1).strip()
            if os.path.exists(img_path):
                try:
                    pdf.ln(5)
                    # Scale image width to fit page nicely
                    pdf.image(img_path, x=15, y=None, w=180)
                    pdf.ln(5)
                    print(f"Successfully embedded image in PDF: {img_path}")
                except Exception as e:
                    print(f"Failed to embed image {img_path}: {e}")
            else:
                print(f"Warning: Image path does not exist: {img_path}")
        else:
            # Render text block as HTML
            html_content = markdown2.markdown(block, extras=["tables", "fenced-code-blocks"])
            try:
                pdf.write_html(html_content)
            except Exception as e:
                print(f"Error during FPDF HTML write: {e}. Appending raw text block.")
                pdf.set_font('helvetica', '', 10)
                pdf.multi_cell(0, 5, block)

    pdf.output(output_pdf_path)
    print(f"Successfully generated PDF: {output_pdf_path}")

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    md_path = os.path.join(root_dir, "blogpost2.md")
    html_path = os.path.join(root_dir, "blogpost2.html")
    pdf_path = os.path.join(root_dir, "blogpost2.pdf")

    if not os.path.exists(md_path):
        print(f"Error: {md_path} not found.")
        sys.exit(1)

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # 1. Compile HTML
    html_content = markdown2.markdown(md_text, extras=["fenced-code-blocks", "tables"])
    full_html = HTML_TEMPLATE.replace("{content}", html_content)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Successfully generated HTML: {html_path}")

    # 2. Compile PDF
    md_to_pdf(md_text, pdf_path)

if __name__ == "__main__":
    main()
