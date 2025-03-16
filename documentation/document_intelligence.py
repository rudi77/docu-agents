import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

# Set up Azure credentials
endpoint = os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"]
key = os.environ["DOCUMENT_INTELLIGENCE_KEY"]

# Initialize the client
document_analysis_client = DocumentIntelligenceClient(
    endpoint=endpoint, 
    credential=AzureKeyCredential(key)
)

def extract_text_from_pdf(pdf_path):
    # Open and read the PDF file
    with open(pdf_path, "rb") as f:
        document_bytes = f.read()

    # Start the analysis
    poller = document_analysis_client.begin_analyze_document(
        "prebuilt-read", document_bytes
    )
    result = poller.result()

    # Extract and return the text
    extracted_text = []
    for page in result.pages:
        for line in page.lines:
            extracted_text.append(line.content)

    return "\n".join(extracted_text)

# Example usage
pdf_path = "path/to/your/pdf/file.pdf"
ocr_result = extract_text_from_pdf(pdf_path)
print(ocr_result)
