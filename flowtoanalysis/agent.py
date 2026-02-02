import vertexai
import os
from vertexai.generative_models import GenerativeModel, Part
from google.adk.agents import Agent
from google.cloud import storage  # Required for downloading

# Spire Imports
from spire.doc import Document, ImageType
from spire.presentation import Presentation as ppt_Presentation

vertexai.init(project="akhil1demo", location="us-central1")

def download_from_gcs(gcs_uri: str, local_path: str):
    """Downloads a file from GCS to a local path."""
    client = storage.Client()
    # Parse gs://bucket/path/to/file
    path_parts = gcs_uri.replace("gs://", "").split("/")
    bucket_name = path_parts[0]
    blob_name = "/".join(path_parts[1:])
    
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    print(f"Downloaded {gcs_uri} to {local_path}")

def convert_document_to_sql(gcs_uri: str) -> str:
    model = GenerativeModel("gemini-2.0-flash")
    file_ext = os.path.splitext(gcs_uri)[1].lower()
    
    # Use the /tmp/ directory for cloud execution
    local_temp_path = f"/tmp/input_file{file_ext}"
    download_from_gcs(gcs_uri, local_temp_path)

    prompt = "Analyze the flowchart in this document and provide the SQL for each step."

    try:
        if file_ext in [".png", ".jpg", ".jpeg", ".pdf"]:
            file_part = Part.from_uri(mime_type="application/pdf" if file_ext == ".pdf" else "image/png", uri=gcs_uri)
            return model.generate_content([prompt, file_part]).text

        elif file_ext == ".pptx":
            ppt = ppt_Presentation()
            ppt.LoadFromFile(local_temp_path) # Now the file exists locally!
            images = []
            for i in range(ppt.Slides.Count):
                image_stream = ppt.Slides[i].SaveAsImage()
                images.append(Part.from_data(data=image_stream.ToArray(), mime_type="image/png"))
            return model.generate_content([prompt] + images).text

        elif file_ext == ".docx":
            doc = Document()
            doc.LoadFromFile(local_temp_path) # Now the file exists locally!
            images = []
            for i in range(doc.GetPageCount()):
                image_stream = doc.SaveImageToStreams(i, ImageType.Bitmap)
                images.append(Part.from_data(data=image_stream.ToArray(), mime_type="image/png"))
            return model.generate_content([prompt] + images).text
            
    finally:
        # Cleanup: Remove temp file after processing to save space
        if os.path.exists(local_temp_path):
            os.remove(local_temp_path)

    return f"Unsupported format: {file_ext}"

root_agent = Agent(
    name="universal_sql_agent",
    model="gemini-2.0-flash",
    instruction="Translate flowcharts in any document to SQL. I handle GCS downloads automatically.",
    tools=[convert_document_to_sql]
)
