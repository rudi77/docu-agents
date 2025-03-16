import os
import argparse
from pathlib import Path
import logging
from collections import OrderedDict

from smolagents import CodeAgent, LiteLLMModel, ToolCallingAgent
from src.tools.azure_ocr_tool import AzureOCRTool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MARKDOWN_AGENT_DESCRIPTION = """
This agent can extract text from pdf or image documents using OCR and convert it into a markdown format.
You have access to the azure_ocr tool which can extract text from documents.
When processing a document:
1. Use the azure_ocr tool to extract text from the document
2. Format the extracted text into a clean markdown structure
3. Return the formatted markdown string
"""

EXTRACT_STRUCTURED_DATA_AGENT_DESCRIPTION = """
You are a structured data extraction agent. Your task is to:
1. Take a markdown string as input
2. Extract all relevant invoice details as structured json from the markdown
3. Return the json
"""

MANAGER_AGENT_DESCRIPTION = """
You are a document processing manager. Your task is to:
1. Take a document file path as input
2. Use the markdown_agent to extract and format the text
3. Use the structured_data_agent to extract invoice details as structured json from the markdown
4. Return the json
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
        task = f"""Process the document at {args.file_path} and return the results as a well-formatted markdown string.
        Use the markdown_agent to extract and format the text.
        Use the structured_data_agent to extract invoice details as structured json from the markdown.
        Return the json."""

        # Run the task
        result = manager_agent.run(task)
        
        # Print the result
        if result:
            print(result)
            
            # Save to file if output path specified
            if args.output:
                output_path = Path(args.output)
                output_path.write_text(str(result))
                logger.info(f"Output saved to {output_path}")
                
        return 0
                
    except Exception as e:
        logger.error(f"Error processing document: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main()) 