# Document Processing System

A flexible document processing system that uses AI agents to extract structured data from documents.

## Features

- Process various document types (PDFs, scans, images)
- Extract structured data automatically
- Flexible output format (JSON)
- Support for different LLM models
- Simple command-line interface

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd docu-agents
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
```bash
# Create a .env file with your API keys
OPENAI_API_KEY=your_key_here
AZURE_VISION_KEY=your_key_here
AZURE_VISION_ENDPOINT=your_endpoint_here
```

## Usage

Process a document using the command line interface:

```bash
# Basic usage
python src/main.py path/to/your/document.pdf

# Save output to a file
python src/main.py path/to/your/document.pdf -o output.json

# Use a different model
python src/main.py path/to/your/document.pdf -m gpt-3.5-turbo

# Use a custom API endpoint
python src/main.py path/to/your/document.pdf --api-base http://your-api-endpoint
```

### Command Line Options

- `file_path`: Path to the document to process (required)
- `-o, --output`: Path to save the extracted data (optional)
- `-m, --model`: Name of the LLM model to use (default: gpt-4)
- `--api-base`: Base URL for the API (optional)

## Example Output

```json
{
  "invoice_number": "12345",
  "date": "2024-03-15",
  "total_amount": "1250.00",
  "currency": "EUR",
  "line_items": [
    {
      "description": "Product A",
      "quantity": 2,
      "unit_price": "500.00",
      "total": "1000.00"
    }
  ]
}
```

## Architecture

The system uses a hierarchical multi-agent approach:

1. **Document Conversion**: Converts documents into processable text using OCR
2. **Data Extraction**: Extracts structured data from the text
3. **Workflow Management**: Orchestrates the process using LLM-powered agents

## Best Practices

- Focus on extracting information, not enforcing strict formats
- Trust LLM capabilities for text understanding
- Keep the system flexible for different document types
- Use configuration over code for business logic
- Minimize dependencies and complexity

## Error Handling

The application handles common errors:
- Invalid file paths
- API authentication issues
- Document processing failures
- Invalid output formats

Errors are logged with helpful messages to assist in troubleshooting.

## Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Your chosen license] 