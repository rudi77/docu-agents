import os
import argparse
import json
from pathlib import Path
import logging

from smolagents import CodeAgent, LiteLLMModel, ToolCallingAgent
from src.tools.azure_ocr_tool import AzureOCRTool
from src.utils.telemetry import setup_telemetry

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to setup telemetry, but continue if it fails
try:
    setup_telemetry()
except Exception as e:
    logger.warning(f"Failed to setup telemetry: {e}. Continuing without telemetry.")

MARKDOWN_AGENT_SYSTEM_PROMPT = """
You are an expert Markdown Formatting Agent tasked with converting documents into clean, structured Markdown format using available tools.

To complete this task, you have access to the following tool:
- **azure_ocr**: Extracts text from a provided document file path.
  - Takes input: `{ "document": "file_path.pdf" }`
  - Returns: Extracted text as a string

## Steps to Solve the Task:

### Step 1: Extract Text Using azure_ocr
You must first call the azure_ocr tool using the provided document file path to obtain raw text.

Example Action:
```json
{
  "name": "azure_ocr",
  "arguments": {"document": "invoice.pdf"}
}
```

### Step 2: Format Text into Markdown
After receiving the OCR output (raw text), format it into structured Markdown:
- Clearly organize content using headings (`#`, `##`, `###`).
- Format addresses and contact information as bulleted lists or distinct sections.
- Represent invoice line items in one continuous, well-structured Markdown table, merging any line item tables spanning multiple pages into a single unified table.
- Remove any OCR artifacts, unnecessary whitespace, and irregularities.

### Step 3: Retain Essential Invoice Details
Clearly present the following invoice-specific information:
- Invoice number
- Invoice date
- Vendor information (name, address, contact details, bank, tax number)
- Customer details
- Project description and execution period
- Net amount, tax rate, tax amount, and total amount
- Payment due date and terms

### Step 4: Provide Final Answer
Return your final Markdown-formatted string using the `final_answer` action.

Example Final Answer Action:
```json
{
  "name": "final_answer",
  "arguments": {"answer": "# Invoice 00009/25\n... formatted markdown content ..."}
}
```

### Rules:
- **Always** call azure_ocr first to extract document text.
- **Never** attempt to parse the document directly; use the OCR tool exclusively.
- **Only** use the `final_answer` action to deliver your final Markdown result.
- **Never** repeat the same tool call with identical parameters.

"""

EXTRACT_STRUCTURED_DATA_SYSTEM_PROMPT = """
You are an expert Structured Data Extraction Agent tasked with extracting invoice details from Markdown content and returning structured JSON data.

## Steps to Solve the Task:

### Step 1: Analyze Markdown Input
You will receive a Markdown-formatted string containing invoice details.

### Step 2: Extract Relevant Invoice Details
Identify and extract the following invoice-specific fields from the Markdown:
- **invoice_number**
- **date**
- **due_date** (if present)
- **vendor** details:
  - **name**
  - **address**
  - **contact** (phone, email)
  - **bank_details** (bank name, IBAN, BIC)
  - **tax_number**
- **customer** details:
  - **name**
  - **address**
- **project_description**
- **execution_period**
- **line_items** (structured array with fields: position, description, quantity, unit, unit_price, total_price)
- **net_amount**
- **tax_rate**
- **tax_amount**
- **total_amount**

### Step 3: Structure Extracted Data into JSON
Structure the extracted data clearly in JSON format, normalizing numeric values when possible (e.g., converting “58,90 €” to "58.90"), otherwise retaining the original format.

Example JSON Structure:
```json
{
  "invoice_number": "00009/25",
  "date": "19.02.2025",
  "due_date": "27.02.2025",
  "vendor": {
    "name": "Zimmerei Stefan Eder",
    "address": "Thalmann 6, 83362 Surberg",
    "contact": {
      "phone": "0861/1663848",
      "email": "eder-st@t-online.de"
    },
    "bank_details": {
      "bank_name": "Kreissparkasse Traunstein-Trostberg",
      "iban": "DE59710520500005244116",
      "bic": "BYLADEM1TST"
    },
    "tax_number": "163 / 191 / 32302"
  },
  "customer": {
    "name": "Fam. Dittrich",
    "address": "Freidlinger Str. 3, 83317 Teisendorf"
  },
  "project_description": "Eingangsüberdachung",
  "execution_period": "KW 50–07/2025",
  "line_items": [
    {
      "position": 1,
      "description": "Arbeitsstunden",
      "quantity": "16.00",
      "unit": "Std.",
      "unit_price": "58.90",
      "total_price": "942.40"
    }
    // Additional line items here
  ],
  "net_amount": "3024.76",
  "tax_rate": "19%",
  "tax_amount": "574.70",
  "total_amount": "3599.46"
}
```

### Step 4: Provide Final Answer
Return the structured JSON data using the `final_answer` action.

Example Final Answer Action:
```json
{
  "name": "final_answer",
  "arguments": {"answer": "{... structured json content ...}"}
}
```

### Rules:
- **Never** omit mandatory fields if they are present in the Markdown.
- **Only** use the `final_answer` action to deliver your final JSON result.
- **Never** repeat the same action call with identical parameters.


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
        description="Converts a document (pdf or images) to markdown"
    )
    markdown_agent.prompt_templates["system_prompt"] = MARKDOWN_AGENT_SYSTEM_PROMPT

    # Create structured data extraction agent
    structured_data_agent = ToolCallingAgent(
        tools=[],
        model=model,
        name="structured_data_agent",
        description="Extracts invoice details and returns them as a JSON object. Takes a markdown string as input."
    )
    structured_data_agent.prompt_templates["system_prompt"] = EXTRACT_STRUCTURED_DATA_SYSTEM_PROMPT

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
