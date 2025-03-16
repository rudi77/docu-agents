import pytest
from unittest.mock import Mock, patch
import tempfile
from types import SimpleNamespace
from smolagents.models import ChatMessage, MessageRole
from src.agents.markdown_agent import MarkdownAgent
from src.tools.azure_ocr_tool import AzureOCRTool

@pytest.fixture
def mock_model():
    model = Mock()
    model.last_input_token_count = 0
    model.last_output_token_count = 0
    return model

@pytest.fixture
def markdown_agent(mock_model):
    mock_ocr_tool = Mock(spec=AzureOCRTool)
    mock_ocr_tool.name = "azure_ocr"
    mock_ocr_tool.description = "Extracts text from documents using Azure OCR"
    
    agent = MarkdownAgent(
        model=mock_model,
        azure_ocr_tool=mock_ocr_tool,
        max_steps=3
    )
    return agent

def test_markdown_agent_initialization(markdown_agent):
    """Test proper initialization of the MarkdownAgent."""
    assert markdown_agent.name == "markdown_agent"
    assert markdown_agent.description == "Converts documents into structured markdown format using OCR and LLM"
    assert len(markdown_agent.tools) == 2  # OCR tool + final_answer tool
    assert "azure_ocr" in markdown_agent.tools
    assert "final_answer" in markdown_agent.tools
    assert markdown_agent.max_steps == 3

def test_markdown_agent_process_document(markdown_agent, mock_model):
    """Test document processing with the MarkdownAgent."""
    # Create a temporary PDF file
    with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
        # Mock OCR tool response
        ocr_response = [
            {
                "page": 1,
                "text": "Sample Invoice\nDate: 2024-03-15\nAmount: $500",
                "confidence": 0.95
            }
        ]
        markdown_agent.tools["azure_ocr"].side_effect = lambda **kwargs: ocr_response

        # Mock model responses
        tool_call = SimpleNamespace(
            id="call_1",
            function=SimpleNamespace(
                name="azure_ocr",
                arguments={"file_path": temp_file.name}
            )
        )
        
        final_tool_call = SimpleNamespace(
            id="call_2",
            function=SimpleNamespace(
                name="final_answer",
                arguments={
                    "answer": """# Sample Invoice

**Date:** 2024-03-15  
**Amount:** $500"""
                }
            )
        )

        mock_model.side_effect = [
            ChatMessage(
                role=MessageRole.ASSISTANT,
                content="Processing document...",
                tool_calls=[tool_call]
            ),
            ChatMessage(
                role=MessageRole.ASSISTANT,
                content="Converting to markdown...",
                tool_calls=[final_tool_call]
            )
        ]

        # Process document
        result = markdown_agent.process_document(temp_file.name)

        # Verify the result
        assert "# Sample Invoice" in result
        assert "**Date:** 2024-03-15" in result
        assert "**Amount:** $500" in result

def test_markdown_agent_validation(markdown_agent):
    """Test markdown validation functionality."""
    # Valid markdown
    valid_markdown = """# Title

## Section 1
Content with `code` and [link](url).

## Section 2
- List item 1
- List item 2

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
"""
    assert markdown_agent.validate_markdown(valid_markdown) is True

    # Invalid markdown
    invalid_markdown = """# Title
Unmatched `backtick
[Unmatched bracket
"""
    assert markdown_agent.validate_markdown(invalid_markdown) is False

    # Empty markdown
    assert markdown_agent.validate_markdown("") is False
    assert markdown_agent.validate_markdown(None) is False

def test_markdown_agent_error_handling(markdown_agent, mock_model):
    """Test error handling in the MarkdownAgent."""
    with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
        # Mock OCR tool to raise an exception
        markdown_agent.tools["azure_ocr"].side_effect = Exception("OCR processing failed")

        # Mock model responses
        tool_call = SimpleNamespace(
            id="call_1",
            function=SimpleNamespace(
                name="azure_ocr",
                arguments={"file_path": temp_file.name}
            )
        )
        
        final_tool_call = SimpleNamespace(
            id="call_2",
            function=SimpleNamespace(
                name="final_answer",
                arguments={"answer": "Error: OCR processing failed"}
            )
        )

        mock_model.side_effect = [
            ChatMessage(
                role=MessageRole.ASSISTANT,
                content="Processing document...",
                tool_calls=[tool_call]
            ),
            ChatMessage(
                role=MessageRole.ASSISTANT,
                content="Handling error...",
                tool_calls=[final_tool_call]
            )
        ]

        # Process document and expect error message
        result = markdown_agent.process_document(temp_file.name)
        assert "Error: OCR processing failed" in result 