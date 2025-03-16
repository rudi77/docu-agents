from pathlib import Path
from typing import List, Optional
import time
import logging
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from rich.console import Console
from rich.logging import RichHandler
from pydantic import BaseModel

from smolagents import Tool
from src.config.settings import settings

# Configure rich logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("azure_ocr")
console = Console()

class OCRResponse(BaseModel):
    """Model for OCR response data"""
    page_number: int
    text: str
    confidence: float = 1.0  # Default to 1.0 since confidence is not provided by the API

class AzureOCRTool(Tool):
    """Tool for performing OCR using Azure's Document Intelligence API"""
    name = "azure_ocr"
    description = """
    Performs Optical Character Recognition (OCR) on documents using Azure's Document Intelligence API.
    This tool can process PDF documents and images to extract text content.
    The tool handles retries and provides detailed error messages if something goes wrong.
    The tool returns a text string of the extracted text from the document.
    """
    inputs = {
        "file_path": {
            "type": "string",
            "description": "Path to the document file (PDF or image) to process"
        }
    }
    output_type = "string"  # Will return a list of OCRResponse objects

    def __init__(self):
        super().__init__()
        self.max_retries = 3
        self.retry_delay = 1
        self.timeout = 30
        self.endpoint = settings.AZURE_OCR_ENDPOINT
        self.api_key = settings.AZURE_OCR_KEY
        self.is_initialized = False
        
    def setup(self):
        """Initialize the Azure Document Intelligence client"""
        if not self.endpoint or not self.api_key:
            raise ValueError("Azure OCR endpoint and API key must be configured")
        
        self.client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key)
        )
        self.is_initialized = True

    def _process_document(self, file_path: Path, retry_count: int = 0) -> dict:
        """Process document with retry logic"""
        try:
            with open(file_path, "rb") as file:
                document_bytes = file.read()
                poller = self.client.begin_analyze_document(
                    "prebuilt-read",
                    document_bytes
                )
                result = poller.result()
                return result
        except Exception as e:
            if retry_count < self.max_retries:
                logger.warning(f"Request failed, retrying ({retry_count + 1}/{self.max_retries}): {str(e)}")
                time.sleep(self.retry_delay * (2 ** retry_count))  # Exponential backoff
                return self._process_document(file_path, retry_count + 1)
            raise Exception(f"Failed to process document after {self.max_retries} attempts: {str(e)}")

    def _extract_text_from_result(self, result: dict) -> str:
        """Extract text and metadata from OCR result and return it as a text string"""
        
        text = ""
        text_lines = []        
        # Process each page
        for page_idx, page in enumerate(result.pages, 1):
            text_lines.append(f"Page {page_idx}\n")
            # Extract lines from the page
            for line in page.lines:
                text_lines.append(line.content)

        text = "\n".join(text_lines)

        return text

    def forward(self, file_path: str) -> str:
        """
        Process a document using Azure Document Intelligence.
        
        Args:
            file_path: Path to the document file to process
            
        Returns:
            A text string of the extracted text from the document
        """
        if not self.is_initialized:
            self.setup()

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Processing document: {file_path}")
        
        try:
            # Process document
            result = self._process_document(file_path)
            
            # Extract and format text
            responses = self._extract_text_from_result(result)
            
            logger.info(f"Successfully processed document with {len(responses)} pages")
            return responses
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise 