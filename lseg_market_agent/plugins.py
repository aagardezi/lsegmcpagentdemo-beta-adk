import os
import re
from typing import Optional
from google.adk.plugins import BasePlugin
from google.adk.events import Event
from google.adk.agents import InvocationContext

# Lazy import to avoid crash if not installed for local-only execution
# google-cloud-storage will be needed for Agent Engine
try:
    from google.cloud import storage
except ImportError:
    storage = None

class ReportGraphFixerPlugin(BasePlugin):
    """
    Intercepts the report agent response, finds images from graphing agent in history,
    saves them to local files OR uploads to Google Cloud Storage (GCS),
    and updates the report markdown with the correct path or URL.
    """
    def __init__(self, output_dir: str = "generated_reports/images", gcs_bucket: Optional[str] = None):
        from dotenv import load_dotenv
        load_dotenv() # Force reading isolat d local .env if uploaded in package bundle
        super().__init__(name="report_graph_fixer")
        self.output_dir = output_dir
        self.gcs_bucket = gcs_bucket or os.environ.get("GRAPH_OUTPUT_BUCKET")

    async def on_event_callback(
        self, *, invocation_context: InvocationContext, event: Event
    ) -> Optional[Event]:
        # Intercept any agent that references graphs
        if not event.content or not event.content.parts:
            return None

        report_text = event.content.parts[0].text
        if not report_text:
            return None

        os.makedirs(self.output_dir, exist_ok=True)

        image_paths = []
        is_using_gcs = False

        # Initialize GCS Client if bucket is configured
        gcs_client = None
        bucket = None
        if self.gcs_bucket:
            if storage is None:
                 print("[Plugin] Error: google-cloud-storage package is missing. Cannot upload to GCS.")
            else:
                 try:
                     gcs_client = storage.Client()
                     bucket = gcs_client.bucket(self.gcs_bucket)
                     is_using_gcs = True
                     print(f"[Plugin] Using GCS bucket: {self.gcs_bucket}")
                 except Exception as e:
                     print(f"[Plugin] Error initializing GCS client: {e}")

        print(f"[Plugin] on_event_callback triggered from {event.author}")
        if is_using_gcs:
            print("[Plugin] GCS mode active")

        # 1. Scan filesystem for generated image files
        # Vertex AI code interpreters and executors save plots as files rather than inline_data
        import glob
        found_files = glob.glob("*.png") + glob.glob("/tmp/*.png")
        print(f"[Plugin] Found {len(found_files)} image files on disk to process: {found_files}")

        for filepath in found_files:
            try:
                filename = os.path.basename(filepath)
                with open(filepath, "rb") as f:
                    image_data = f.read()

                mime = "image/png" # Matplotlib defaults to PNG
                if is_using_gcs and bucket:
                    # Upload to GCS
                    blob_path = f"graphs/{filename}"
                    blob = bucket.blob(blob_path)
                    blob.upload_from_string(image_data, content_type=mime)
                    
                    public_url = f"https://storage.googleapis.com/{self.gcs_bucket}/{blob_path}"
                    image_paths.append(public_url)
                    print(f"[Plugin] Saved graph file to GCS: {public_url}")
                else:
                    # Fallback: Copy to output_dir
                    target_filepath = os.path.join(self.output_dir, filename)
                    with open(target_filepath, "wb") as f:
                        f.write(image_data)
                    image_paths.append(target_filepath)
                    print(f"[Plugin] Copied graph file locally to {target_filepath}")

                # DELETE file from isolate after processing to prevent re-uploading next turn
                os.remove(filepath)
                print(f"[Plugin] Cleaned up temporary isolate file: {filepath}")

            except Exception as e:
                 print(f"[Plugin] Error processing file {filepath}: {e}")

        if not image_paths:
            return None

        # Replace placeholders in report_text
        updated_text = report_text
        pattern = r"!\[.*?\]\(.*?\)"
        matches = list(re.finditer(pattern, updated_text))
        
        if matches and len(matches) <= len(image_paths):
            print(f"[Plugin] Found {len(matches)} image placeholders. Replacing...")
            for match, path in zip(matches, image_paths):
                updated_text = updated_text.replace(match.group(0), f"![Graph]({path})")
        else:
            print(f"[Plugin] Appending {len(image_paths)} graphs at the bottom of the report.")
            updated_text += "\n\n---\n## Generated Graphs\n"
            for path in image_paths:
                updated_text += f"\n![Graph]({path})\n"

        event.content.parts[0].text = updated_text
        return event
