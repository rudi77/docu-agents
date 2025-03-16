from pathlib import Path
from typing import List
from pydantic import BaseModel

from smolagents import Tool

class TextResponse(BaseModel):
    """Model for text response data"""
    text: str

class TextTool(Tool):
    """Tool for reading text files directly"""
    name = "text_reader"
    description = """
    Reads text files directly and returns their content.
    This tool is used for processing plain text files without OCR.
    """
    inputs = {
        "file_path": {
            "type": "string",
            "description": "Path to the text file to process"
        }
    }
    output_type = "object"  # Will return a TextResponse object

    def forward(self, file_path: str) -> TextResponse:
        """
        Read a text file directly.
        
        Args:
            file_path: Path to the text file to process
            
        Returns:
            TextResponse: The text content of the file
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return TextResponse(text=text)
            
        except Exception as e:
            raise Exception(f"Error reading text file: {str(e)}") 