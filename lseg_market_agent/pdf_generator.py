import os

import markdown2
from fpdf import FPDF
from google.genai import types


class ReportPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12)
        self.cell(0, 10, 'LSEG Market Intelligence Report', border=False, align='C')
        self.ln(10)
        self.line(10, 20, 200, 20) # Draw a line under header
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

def _cleanse_text(text: str) -> str:
    """Bulletproof cleanser for FPDF core fonts fallback.
    Replaces common non-ASCII characters & implements absolute crash guard."""
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

    fixed_chars = []
    for char in text:
        try:
            # Helvetica in fpdf2 uses standard latin-1 set
            char.encode('latin-1')
            fixed_chars.append(char)
        except UnicodeEncodeError:
            fixed_chars.append('?') # absolute fallback instead of crashing
    return "".join(fixed_chars)

async def create_pdf_report(
    markdown_content: str,
    image_paths: list = None,
    artifact_name: str = "financial_report.pdf",
    tool_context = None
) -> str:
    """
    Converts Markdown text into a professional PDF report and appends any 
    generated graph visualisations.
    
    Args:
        markdown_content: The markdown text to convert.
        image_paths: Optional list of file paths to generated graph images to append.
        artifact_name: The name of the downloadable session artifact to save.
        tool_context: Optional context automatically injected by the ADK framework.
        
    Returns:
        A confirmation message containing the artifact name.
    """
    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font('helvetica', '', 11)

    # Cleanse markdown content to remove problematic Unicode typography before parsing
    markdown_content = _cleanse_text(markdown_content)

    # STRIP IMAGE TAGS: fpdf2 crashes if write_html parses <img> tags pointing to missing local files.
    import re
    markdown_content = re.sub(r'!\[.*?\]\(.*?\)', '', markdown_content)

    # Convert Markdown to HTML (supporting tables)
    html_content = markdown2.markdown(markdown_content, extras=["tables"])

    try:
        # Use fpdf2's write_html
        pdf.write_html(html_content)
    except Exception as e:
        # Fallback to appending unrendered text on error
        print(f"[PDF Generator] Error during write_html: {e}")
        # Ensure a page is open for multi_cell; write_html failure often leaves state invalid
        try:
             # Try adding a new page in case state of page was rolling back
             pdf.add_page()
        except Exception:
             pass
        pdf.set_font('helvetica', '', 11)
        pdf.multi_cell(0, 10, f"Error rendering HTML template. Appending raw content:\n\n{markdown_content}")

    # Append explicitly passed images
    if image_paths:
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 14)
        pdf.cell(0, 10, 'Generated Visualisations', ln=1)
        pdf.ln(5)

        for img_path in image_paths:
            try:
                # Load from artifact service first
                if tool_context is not None:
                    try:
                        artifact = await tool_context.load_artifact(filename=img_path)
                        if artifact and hasattr(artifact, 'inline_data') and artifact.inline_data:
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img:
                                temp_img.write(artifact.inline_data.data)
                                temp_img_path = temp_img.name
                            pdf.image(temp_img_path, x=10, y=None, w=180)
                            pdf.ln(10)
                            os.remove(temp_img_path) # cleanup
                            print(f"[PDF Generator] Embedded image from artifact: {img_path}")
                            continue
                    except Exception as e:
                        print(f"[PDF Generator] Loading artifact {img_path} failed: {e}. Falling back to workspace.")

                # Fallback to local workspace check
                if not os.path.exists(img_path):
                    print(f"[PDF Generator] Image path does not exist: {img_path}")
                    continue

                pdf.image(img_path, x=10, y=None, w=180)
                pdf.ln(10)
                os.remove(img_path)
            except Exception as e:
                 print(f"[PDF Generator] Failed to embed image {img_path}: {e}")

    # Render purely in-memory
    try:
        bytes_data = pdf.output()
        if tool_context is not None:
            part = types.Part.from_bytes(data=bytes_data, mime_type="application/pdf")
            await tool_context.save_artifact(
                filename=artifact_name,
                artifact=part
            )
            return f"Successfully saved to session artifact: {artifact_name}"
        else:
             fallback_path = f"/tmp/{artifact_name}"
             with open(fallback_path, 'wb') as f:
                 f.write(bytes_data)
             return f"Saved to fallback local disk: {fallback_path}"
    except Exception as e:
         print(f"[PDF Generator] Failed to create PDF in-memory: {e}")
         raise e
