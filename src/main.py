import os
import argparse
import json
from pathlib import Path
import logging
from collections import OrderedDict

from smolagents import CodeAgent, LiteLLMModel, ToolCallingAgent
from src.tools.azure_ocr_tool import AzureOCRTool
from src.utils.telemetry import setup_telemetry

setup_telemetry()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MARKDOWN_AGENT_DESCRIPTION = """
You are a markdown formatting agent. Your task is to:
1. Take a document file path as input
2. Use the azure_ocr tool to extract text from the document
3. Format the extracted text into a clean, well-structured markdown format
4. Return the formatted markdown string

Important: You must use the azure_ocr tool to extract text from the document.
"""

EXTRACT_STRUCTURED_DATA_AGENT_DESCRIPTION = """
You are a structured data extraction agent. Your task is to:
1. Take a markdown string as input
2. Analyze the markdown content to identify key information
3. Extract all relevant invoice details as structured json from the markdown
4. Return the json with the extracted information

The json should include fields like:
- invoice_number
- date
- total_amount
- line_items
- vendor_name
- etc.
"""

MANAGER_AGENT_DESCRIPTION = """
You are a document processing manager. Your task is to:
1. Take a document file path as input
2. First, use the markdown_agent to extract text and format it as markdown
3. Then, use the structured_data_agent to extract invoice details from the markdown
4. Return the extracted structured data

Important: You must use both agents in sequence:
1. First call markdown_agent with the document path
2. Then call structured_data_agent with the markdown output
"""



def setup_agents():
    """Set up the agents for document processing."""
    # Get OpenAI API key from environment variables
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Initialize the model with the API key
    model = LiteLLMModel(
        model_id="gpt-4o-mini",
        api_key=openai_api_key
    )

    # Create OCR tool
    ocr_tool = AzureOCRTool()

    # Create markdown agent
    markdown_agent = ToolCallingAgent(
        tools=[ocr_tool],
        model=model,
        name="markdown_agent",
        description=MARKDOWN_AGENT_DESCRIPTION
    )

    # Create structured data extraction agent
    structured_data_agent = ToolCallingAgent(
        tools=[],
        model=model,
        name="structured_data_agent",
        description=EXTRACT_STRUCTURED_DATA_AGENT_DESCRIPTION
    )

    # Create manager agent
    manager_agent = CodeAgent(
        tools=[],
        model=model,
        managed_agents=[markdown_agent, structured_data_agent],
        description=MANAGER_AGENT_DESCRIPTION
    )

    return manager_agent

def main():
    """Main function to run the document processing."""
    parser = argparse.ArgumentParser(description="Process documents using AI agents")
    parser.add_argument("-f", "--file_path", required=True, help="Path to the document to process")
    parser.add_argument("-o", "--output", help="Path to save the output markdown")
    args = parser.parse_args()

    try:
        # Set up agents
        manager_agent = setup_agents()

        # Process document
        task = f"""Process the document at {args.file_path}:
        1. First, use the markdown_agent to extract text and format it as markdown
        2. Then, use the structured_data_agent to extract invoice details from the markdown
        3. Return the extracted structured data as JSON

        Important: You must use both agents in sequence. Start with markdown_agent to get the markdown text, then use structured_data_agent to extract the data."""

        # Run the task
        result = manager_agent.run(task)
        
        # Print the result
        if result:
            print(result)
            
            # Write as json to file if output path specified
            if args.output:
                output_path = Path(args.output) 
                output_path.write_text(json.dumps(result, indent=4))
                logger.info(f"Output saved to {output_path}")
                
        return 0
                
    except Exception as e:
        logger.error(f"Error processing document: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main()) 