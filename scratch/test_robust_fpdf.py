import subprocess
import sys
import os

# Install fpdf2 and markdown2
subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2", "markdown2", "--index-url", "https://pypi.org/simple/"])

from fpdf import FPDF
import markdown2

def cleanse_text_extended(text: str) -> str:
    """Bulletproof cleanser for FPDF core fonts."""
    # 1. Custom mappings for human readability
    replacements = {
        '\u2013': '-', '\u2014': '-', '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"', '\u2026': '...',
        '\u20ac': 'EUR ', '\u00a3': 'GBP ', '\u00a5': 'JPY ',
        '•': '-', '™': '(TM)', '©': '(C)', '®': '(R)',
        '×': 'x', '¼': '1/4', '½': '1/2', '¾': '3/4',
        '✓': '[x]', 'Δ': 'Delta'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
        
    # 2. Strict encoder fallback: replace any absolute unencodable character with '?'
    fixed_chars = []
    for char in text:
        try:
            # Helvetica in fpdf2 uses standard latin-1 fallback or cp1252
            char.encode('latin-1')
            fixed_chars.append(char)
        except UnicodeEncodeError:
            fixed_chars.append('?') # fallback instead of crashing
    return "".join(fixed_chars)

pdf = FPDF()
pdf.add_page()
pdf.set_font('helvetica', '', 12)

# Test content with MANY unicode symbols
test_content = """
# Risk Analytics Dashboard

- Bullet point • with €50M budget & £10M profit.
- Trademark widget™ © Acme Inc.® 
- Math: 10 × 5 = 50. Growth: Δ2.5%.
- Fractions: ¼, ½, ¾.
- Unhandled symbol: 🚀 Rocket ship.
"""

cleansed = cleanse_text_extended(test_content)
html = markdown2.markdown(cleansed)

try:
    pdf.write_html(html)
    pdf.output("robust_test.pdf")
    print("SUCCESS: PDF created without crash!")
except Exception as e:
    print(f"CRASH: {e}")
