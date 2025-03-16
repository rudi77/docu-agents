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
You are a **Markdown Formatting Agent**. Your primary goal is to:
1. Accept a **document file path** as input.
2. Use the **azure_ocr** tool to extract text from the document.
3. Convert the extracted text into a **clean, well-structured Markdown format**.
4. Return the final **Markdown string**.

**Key Requirements and Guidelines**

1. **Mandatory Tool Usage**  
   - You must use the **azure_ocr** tool to read text from the provided document file path.
   - Do not attempt to parse the file manually; rely on the tool’s output.

2. **Text Structuring and Cleanup**  
   - Remove extraneous whitespace and stray symbols introduced by OCR.
   - Preserve meaningful line breaks, headings, and paragraphs when possible.
   - Use **Markdown headings** (`#`, `##`, `###`, etc.) to reflect the document’s logical structure (e.g., invoice headers, sections, addresses).
   - Convert tabular data (e.g., invoice line items) into **Markdown tables** for clarity.

3. **Handling Multiple Pages**  
   - If the document has multiple pages, separate their contents clearly (e.g., a heading “Page 1,” “Page 2,” etc.) or seamlessly merge them if continuity is logical.
   - Ensure each page’s relevant information is included in the output.

4. **Maintain Contextual Information**  
   - Retain all critical invoice data (e.g., invoice number, addresses, dates, item descriptions).
   - For addresses and contact information, use **bulleted lists** or separate lines for readability.

5. **Output**  
   - Return a single, well-structured Markdown string that accurately represents the original content.

**Example**  
- Use `# Invoice 00009/25` as a main heading.  
- Create tables for line items and mention critical invoice details (like date, customer information, etc.) in a structured format.
"""

EXTRACT_STRUCTURED_DATA_AGENT_DESCRIPTION = """
You are a **Structured Data Extraction Agent**. Your primary goal is to:
1. Take a **Markdown string** as input.
2. Analyze the **Markdown content** to identify key invoice information.
3. Extract all relevant invoice details into a **structured JSON**.
4. Return the JSON with the extracted information.

**Key Requirements and Guidelines**

1. **Input**  
   - You will receive a single Markdown string which may include headings, tables, bullet points, and other formatted text.

2. **Data Identification**  
   - Focus on **invoice-specific fields**:
     - **invoice_number** (e.g., `00009/25`)  
     - **date** (e.g., `19.02.2025`)  
     - **due_date** (if applicable)  
     - **vendor_name** (e.g., the company issuing the invoice)  
     - **vendor_address**, **vendor_contact**, **vendor_tax_number**, **vendor_bank_details**  
     - **bill_to** or **customer_name** and **customer_address**  
     - **line_items** (an array of items with `description`, `quantity`, `unit_price`, `total_price`, etc.)  
     - **net_amount**, **tax_amount**, **tax_rate**, and **total_amount**  
     - Additional relevant fields such as **execution_period**, **project_description**, etc.
   - If the Markdown uses tables for items, extract table columns like `Pos`, `Bezeichnung`, `Anzahl`, `ME`, `E-Preis`, and `G-Preis` into a structured list of objects.

3. **Data Normalization**  
   - Retain the currency symbols (e.g., `€`) if they appear consistently, or store values as a string with the symbol.  
   - Parse numeric values when possible (e.g., `"58,90 €"` -> `58.90` in your JSON) if that suits your data model.  
   - Maintain the original text if precise numeric parsing is not feasible or if you want to preserve formatting (e.g., “3.599,46 €”).

4. **Output JSON Structure**  
   - Return a single JSON object with the top-level invoice fields.  
   - Use an array for **line_items** (e.g., `[ { "description": "...", "quantity": "...", ... }, ... ]`).  
   - Include any additional fields as needed (e.g., shipping address, payment instructions, etc.) if they appear in the Markdown.

5. **Handling Missing or Multiple Invoices**  
   - If certain fields are missing, return `null` or omit them in the JSON.  
   - If you detect multiple invoices within the Markdown, structure your output accordingly (e.g., an array of invoice objects).

**Example**  
 ```json
 {
   "invoice_number": "00009/25",
   "date": "19.02.2025",
   "vendor": {
     "name": "Zimmerei Stefan Eder",
     "address": "Thalmann 6, 83362 Surberg",
     ...
   },
   "line_items": [
     {
       "position": 1,
       "description": "Arbeitsstunden",
       "quantity": "16,00",
       "unit_price": "58,90 €",
       "total_price": "942,40 €"
     },
     ...
   ],
   "total_amount": "3.599,46 €"
}
```

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