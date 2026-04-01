import subprocess
import sys

# Install fpdf2
subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2", "--index-url", "https://pypi.org/simple/"])

from fpdf import FPDF
import os

class MYPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12)
        self.cell(0, 10, 'Financial Report', border=True, align='C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

pdf = MYPDF()
pdf.add_page()
pdf.set_font('helvetica', '', 12)

# Add some text
pdf.multi_cell(0, 10, "This is a test report.\nHere is some numerical analysis.")

# Add an image (I'll download a placeholder just to test)
import urllib.request
try:
    urllib.request.urlretrieve("https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png", "test_image.png")
    pdf.image("test_image.png", x=10, y=None, w=100)
    print("Image added successfully")
except Exception as e:
    print(f"Error adding image: {e}")

pdf.output("test_report.pdf")
print("PDF created successfully")
if os.path.exists("test_report.pdf"):
    print("File exists")
else:
    print("File not found")
