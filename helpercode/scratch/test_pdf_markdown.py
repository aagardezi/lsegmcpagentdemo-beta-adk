import subprocess
import sys

# Install fpdf2 and markdown2
subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2", "markdown2", "--index-url", "https://pypi.org/simple/"])

from fpdf import FPDF
import markdown2
import os

class MYPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12)
        self.cell(0, 10, 'Financial Report', border=True, align='C')
        self.ln(20)

pdf = MYPDF()
pdf.add_page()
pdf.set_font('helvetica', '', 11)

markdown_text = """
# Executive Summary
This is a test report explaining investment metrics.

## Key Findings
- **Revenue**: Up 20%
- **EPS**: $3.45 (Analysts expected $3.20)

### Graphs & Visuals
Below is a graph that was generated.

![Test Image](https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png)

### Table Test
| Metric | Value |
| --- | --- |
| Revenue | $100M |
| Net Income | $10M |

"""

# Convert markdown to HTML
html_content = markdown2.markdown(markdown_text, extras=["tables"])
print("HTML CONTENT:")
print(html_content)

# Add HTML to PDF
try:
    # fpdf2 has write_html
    pdf.write_html(html_content)
    print("HTML write successful")
except Exception as e:
    print(f"Error writing HTML: {e}")

pdf.output("test_report_html.pdf")
print("PDF created successfully")
if os.path.exists("test_report_html.pdf"):
    print("File exists")
else:
    print("File not found")
