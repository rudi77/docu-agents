import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes, ReadOperationResult

from src.tools.azure_ocr_tool import AzureOCRTool, OCRResponse

@pytest.fixture
def mock_settings():
    with patch("src.tools.azure_ocr_tool.settings") as mock_settings:
        mock_settings.AZURE_OCR_ENDPOINT = "https://test.cognitiveservices.azure.com/"
        mock_settings.AZURE_OCR_KEY = "test_key"
        mock_settings.LOG_LEVEL = "INFO"
        yield mock_settings

@pytest.fixture
def mock_cv_client():
    with patch("src.tools.azure_ocr_tool.ComputerVisionClient") as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def ocr_tool(mock_settings, mock_cv_client):
    tool = AzureOCRTool()
    tool.setup()  # This will use the mock client
    return tool

def test_tool_initialization(ocr_tool):
    """Test that the tool initializes with correct attributes"""
    assert ocr_tool.name == "azure_ocr"
    assert isinstance(ocr_tool.description, str)
    assert "file_path" in ocr_tool.inputs
    assert ocr_tool.output_type == "array"
    assert ocr_tool.max_retries == 3
    assert ocr_tool.retry_delay == 1
    assert ocr_tool.timeout == 30

def test_make_request_success(ocr_tool, tmp_path):
    """Test successful API request"""
    # Create a test file
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"test content")
    
    # Mock the client response
    mock_response = Mock()
    mock_response.headers = {"Operation-Location": "test_operation_url"}
    ocr_tool.client.read_in_stream.return_value = mock_response
    
    operation_location = ocr_tool._make_request(test_file)
    assert operation_location == "test_operation_url"

def test_make_request_with_retry(ocr_tool, tmp_path):
    """Test request retry on failure"""
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"test content")
    
    # First call fails, second succeeds
    mock_response = Mock()
    mock_response.headers = {"Operation-Location": "test_operation_url"}
    ocr_tool.client.read_in_stream.side_effect = [Exception("API Error"), mock_response]
    
    operation_location = ocr_tool._make_request(test_file)
    assert operation_location == "test_operation_url"
    assert ocr_tool.client.read_in_stream.call_count == 2

def test_get_operation_result_success(ocr_tool):
    """Test successful operation result retrieval"""
    mock_result = Mock(spec=ReadOperationResult)
    mock_result.status = OperationStatusCodes.succeeded
    
    ocr_tool.client.get_read_result.return_value = mock_result
    
    result = ocr_tool._get_operation_result("test_operation_url")
    assert result == mock_result

def test_extract_text_from_result(ocr_tool):
    """Test text extraction from API result"""
    # Create mock result with sample data
    mock_line = Mock()
    mock_line.text = "Sample text"
    mock_line.appearance.confidence = 0.95
    
    mock_page = Mock()
    mock_page.lines = [mock_line]
    
    mock_result = Mock()
    mock_result.analyze_result = Mock()
    mock_result.analyze_result.read_results = [mock_page]
    
    responses = ocr_tool._extract_text_from_result(mock_result)
    
    assert len(responses) == 1
    assert isinstance(responses[0], OCRResponse)
    assert responses[0].page_number == 1
    assert responses[0].text == "Sample text"
    assert responses[0].confidence == 0.95

@pytest.mark.integration
def test_process_document_integration(ocr_tool, tmp_path):
    """Integration test for document processing"""
    # Create a test PDF file
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"test content")
    
    # Mock the read_in_stream response
    mock_response = Mock()
    mock_response.headers = {"Operation-Location": "test_operation_url"}
    ocr_tool.client.read_in_stream.return_value = mock_response
    
    # Mock the get_read_result response
    mock_line = Mock()
    mock_line.text = "Sample text"
    mock_line.appearance.confidence = 0.95
    
    mock_page = Mock()
    mock_page.lines = [mock_line]
    
    mock_result = Mock(spec=ReadOperationResult)
    mock_result.status = OperationStatusCodes.succeeded
    mock_result.analyze_result = Mock()
    mock_result.analyze_result.read_results = [mock_page]
    
    ocr_tool.client.get_read_result.return_value = mock_result
    
    # Process the document
    responses = ocr_tool(str(test_file))
    
    assert len(responses) == 1
    assert responses[0].text == "Sample text"
    assert responses[0].confidence == 0.95 