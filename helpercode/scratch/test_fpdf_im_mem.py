import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2", "--index-url", "https://pypi.org/simple/"])

from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font('helvetica', '', 12)
pdf.cell(0, 10, 'In-Memory Test')

try:
    # Test if we can get bytes directly
    # fpdf2 updated output() to return bytes if no dest or filename is provided in some versions
    out2 = pdf.output()
    if isinstance(out2, bytearray) or isinstance(out2, bytes):
        print("SUCCESS: pdf.output() returns bytes directly")
    else:
        print(f"pdf.output() returned: {type(out2)}")
except Exception as e:
    print(f"Error calling output(): {e}")
