import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2", "--index-url", "https://pypi.org/simple/"])

from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font('helvetica', '', 12)

broken_image_html = '<p>Testing broken image:</p><img src="nonexistent_image_123456.png" />'

try:
    print("Attempting write_html with broken image...")
    pdf.write_html(broken_image_html)
    print("SUCCESS: write_html tolerated broken image!")
except Exception as e:
    print(f"CRASH: write_html fails on broken image: {e} (Type: {type(e)})")

try:
    pdf.output("test_broken_img.pdf")
except Exception as e:
    print(f"Output Crash: {e}")
