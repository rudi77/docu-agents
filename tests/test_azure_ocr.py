import unittest
import os
from pathlib import Path

from src.tools.azure_ocr_tool import AzureOCRTool

class TestAzureOCR(unittest.TestCase):
    def setUp(self):
        # Initialize the OCR tool
        self.ocr_tool = AzureOCRTool()
        
        # Set up test file path
        self.test_pdf = Path(r"C:\Users\rudi\Documents\Private\Rechnungen\2025\Receipt_Zimmerei_Stefan_Eder_2025-02-21_133024.pdf")
        
        # Ensure the test file exists
        self.assertTrue(self.test_pdf.exists(), f"Test PDF file not found at {self.test_pdf}")

    def test_ocr_processing(self):
        """Test processing a real PDF document with Azure OCR."""
        try:
            # Process the document
            responses = self.ocr_tool.forward(str(self.test_pdf))
            
            # Basic validation
            self.assertIsNotNone(responses, "OCR response should not be None")
            self.assertIsInstance(responses, list, "OCR response should be a list")
            self.assertTrue(len(responses) > 0, "OCR response should contain at least one page")
            
            # Print the extracted text for manual verification
            print("\nExtracted text from PDF:")
            for response in responses:
                print(f"\nPage {response.page_number} (confidence: {response.confidence:.2f}):")
                print("-" * 80)
                print(response.text)
                print("-" * 80)
                
                # Additional validation for each page
                self.assertIsInstance(response.page_number, int, "Page number should be an integer")
                self.assertIsInstance(response.text, str, "Text should be a string")
                self.assertIsInstance(response.confidence, float, "Confidence should be a float")
                self.assertTrue(0 <= response.confidence <= 1, "Confidence should be between 0 and 1")
                self.assertTrue(len(response.text) > 0, "Extracted text should not be empty")
                
        except Exception as e:
            self.fail(f"OCR processing failed with error: {str(e)}")

if __name__ == '__main__':
    unittest.main() 