# jom-QA Engine

The core AI-powered QA automation engine for jom-QA. Parses SRS PDF documentation locally and converts them into AI-optimized JSON specifications, reducing AI API token usage by up to 80%. Features professional Playwright integration and intelligent QA workflows.

## 🚀 Features

### Core Capabilities
- **AI-Optimized Specifications**: Converts SRS to token-optimized JSON specs inspired by spec-up
- **Playwright Integration**: Professional browser automation for end-to-end testing
- **Intelligent QA Workflows**: Adaptive test execution with priority-based scheduling
- **Token Optimization**: Reduces AI consumption by up to 80% through smart preprocessing
- **Enhanced PDF Parsing**: Robust SRS PDF parser with configurable patterns
- **Error Handling**: Comprehensive error handling and validation
- **Logging System**: Built-in logging for debugging and monitoring
- **Configuration Management**: Flexible configuration via file or environment variables
- **REST API**: FastAPI-based server for remote parsing and AI spec generation
- **Multiple Pattern Support**: Supports various SRS formats (FR-XXX, REQ-XXX, numbered sections, etc.)
- **Priority Extraction**: Automatically extracts requirement priorities
- **Metadata Tracking**: Tracks parsing statistics and version information
- **Unit Tests**: Comprehensive test coverage

### AI Specification Features
- **Structured Test Cases**: Automated test case generation from requirements
- **Priority-Based Testing**: Critical path identification and execution
- **Token Estimation**: Real-time token consumption estimates
- **Cross-References**: Internal and external specification references
- **Quality Metrics**: Automation coverage and risk scoring
- **Test Matrix Generation**: Comprehensive test coverage planning

## 📂 Project Structure

```text
jom-qa/
│
├── core/
│   ├── __init__.py
│   ├── parser.py               # Enhanced SRS PDF to Structural JSON parser
│   ├── ai_spec.py              # AI-optimized specification format
│   ├── playwright_automation.py # Playwright integration for browser automation
│   └── qa_workflow.py          # Professional QA workflow engine
│
├── api/
│   ├── __init__.py
│   └── main.py                 # FastAPI server with AI spec endpoints
│
├── reporters/
│   ├── __init__.py
│   └── base_reporter.py        # Abstract interface for bug reporting adapters
│
├── tests/
│   ├── __init__.py
│   ├── test_parser.py          # Unit tests for parser
│   └── test_ai_spec.py         # Unit tests for AI spec format
│
├── examples/
│   ├── ai_spec_example.py      # Example: Generate AI-optimized specs
│   ├── playwright_example.py   # Example: Playwright automation
│   └── qa_workflow_example.py # Example: Complete QA workflow
│
├── config.py                   # Configuration management
├── config.json                 # Default configuration file
├── srs_test.pdf                # Sample SRS document
├── run_test_parser.py          # Quick playground execution script
├── requirements.txt
└── README.md
```

## 🔧 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for automation features)
playwright install
```

## 📖 Usage

### Generate AI-Optimized Specifications

```python
from core import LocalSRSParser
from config import get_config
import json

# Load configuration
config = get_config()
config.setup_logging()

# Initialize parser
parser = LocalSRSParser("srs_test.pdf")

# Generate AI-optimized specification
ai_spec = parser.to_ai_spec(optimize_tokens=True, target_tokens=4000)

# Get token estimates
token_estimate = ai_spec.get_token_estimate()
print(f"Estimated tokens: {token_estimate['estimated_tokens']}")

# Save AI spec
parser.save_ai_spec("output/ai_spec.json")
```

### Playwright Automation

```python
import asyncio
from core import PlaywrightAutomation, TestCase, TestStep, ActionType, SelectorType

async def run_test():
    automation = PlaywrightAutomation(headless=True)
    await automation.start()
    
    # Create test case
    test_case = TestCase(
        test_id="TC-001",
        name="Login Test",
        steps=[
            TestStep(action=ActionType.NAVIGATE, value="https://example.com"),
            TestStep(action=ActionType.FILL, selector="#email", value="test@example.com"),
            TestStep(action=ActionType.CLICK, selector="#submit")
        ],
        expected_result="Login successful"
    )
    
    # Execute test
    result = await automation.execute_test_case(test_case)
    print(f"Test status: {result.status}")
    
    await automation.stop()

asyncio.run(run_test())
```

### Professional QA Workflow

```python
import asyncio
from core import QAWorkflow, BrowserType

async def run_workflow():
    workflow = QAWorkflow()
    
    # Load SRS and convert to AI spec
    await workflow.load_srs("srs_test.pdf", optimize_tokens=True)
    
    # Run intelligent workflow
    results = await workflow.run_intelligent_workflow()
    
    # Generate report
    report = workflow.generate_execution_report()
    print(f"Pass rate: {report['summary']['overall_pass_rate']:.1f}%")
    
    await workflow.cleanup()

asyncio.run(run_workflow())
```

### Custom Configuration

```python
from core import LocalSRSParser, ParserConfig

# Create custom parser configuration
custom_config = ParserConfig(
    extract_tables=True,
    module_patterns=[
        r'(?i)(?:Module|Section)\s*\d*:\s*(.*)',
        r'(?i)^\s*\d+\.\s+([^.]+)'
    ],
    requirement_patterns=[
        r'(FR-\d+)\s*:\s*(.*)',
        r'(REQ-\d+)\s*:\s*(.*)'
    ]
)

# Initialize parser with custom config
parser = LocalSRSParser("srs_test.pdf", config=custom_config)
structured_json = parser.parse()
```

### Save to JSON

```python
# Save parsed data to file
output_path = parser.save_to_json("output/srs_parsed.json")
```

### Start API Server

```bash
# Start the FastAPI server
python -m api.main

# Or use uvicorn directly
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints

- `POST /parse` - Parse SRS PDF from file path
- `POST /upload` - Upload and parse PDF file
- `POST /ai-spec` - Generate AI-optimized specification from PDF
- `POST /ai-spec/upload` - Upload PDF and generate AI-optimized spec
- `GET /ai-spec/token-estimate/{job_id}` - Get token consumption estimate
- `GET /result/{job_id}` - Retrieve parsed result
- `DELETE /result/{job_id}` - Delete parsed result
- `GET /health` - Health check endpoint

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=core --cov-report=html
```

## ⚙️ Configuration

Configuration can be provided via:

1. **config.json file** (default)
2. **Environment variables**

### Environment Variables

- `PARSER_EXTRACT_TABLES` - Enable table extraction (true/false)
- `PARSER_ENCODING` - Text encoding (default: utf-8)
- `API_HOST` - API server host (default: 0.0.0.0)
- `API_PORT` - API server port (default: 8000)
- `API_DEBUG` - Enable debug mode (true/false)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_FILE` - Log file path (optional)
- `OUTPUT_DIR` - Output directory (default: output)
- `OPENROUTER_API_KEY` - OpenRouter API key for AI integration
- `OPENROUTER_MODEL` - AI model to use
- `MCP_ENABLED` - Enable MCP integration (true/false)
- `MCP_PORT` - MCP server port (default: 3000)

## 🎯 Supported SRS Formats

The parser supports multiple requirement ID formats:

- `FR-001: Title` - Functional requirements
- `REQ-001: Title` - General requirements
- `1.1 Title` - Numbered requirements
- `ID-123: Title` - Generic ID format

And multiple module formats:

- `Module: Authentication` - Standard module format
- `Section 1: User Management` - Section format
- `# Authentication` - Markdown-style headers
- `1. Authentication` - Numbered sections

## 📊 Output Format

### Basic SRS Format
```json
{
  "project_name": "jom-QA Automated Project",
  "modules": [
    {
      "module_name": "Authentication",
      "requirements": [
        {
          "req_id": "FR-001",
          "title": "User Login",
          "description": "User should be able to login with email and password",
          "priority": "high"
        }
      ]
    }
  ],
  "metadata": {
    "total_lines": 150,
    "parser_version": "2.0",
    "modules_found": 5,
    "requirements_found": 25,
    "lines_processed": 150
  }
}
```

### AI-Optimized Spec Format
```json
{
  "spec_version": "2.0",
  "project_name": "jom-QA Automated Project",
  "modules": [
    {
      "module_id": "authentication",
      "module_name": "Authentication",
      "requirements": [
        {
          "req_id": "FR-001",
          "title": "User Login",
          "description": "User should be able to login with email and password",
          "priority": "high",
          "test_cases": [
            {
              "test_id": "TC-FR-001",
              "name": "Test User Login",
              "test_type": "regression",
              "priority": "high",
              "steps": [
                {
                  "action": "navigate",
                  "value": "/login",
                  "description": "Navigate to login page"
                },
                {
                  "action": "fill",
                  "selector": "#email",
                  "value": "test@example.com",
                  "description": "Enter email"
                }
              ],
              "expected_result": "User logged in successfully",
              "automated": true
            }
          ]
        }
      ]
    }
  ],
  "metadata": {
    "total_requirements": 6,
    "total_test_cases": 6,
    "automation_coverage": 100.0,
    "parser_version": "2.0"
  },
  "token_optimized": true,
  "ai_model_target": "claude-3-haiku"
}
```

## 🔍 System Architecture

- **Local PDF Parsing**: Processes SRS documents locally to reduce API costs
- **AI-Optimized Specifications**: Converts SRS to token-efficient JSON specs inspired by spec-up
- **Playwright Integration**: Professional browser automation for end-to-end testing
- **Intelligent QA Workflows**: Adaptive test execution with priority-based scheduling
- **Flutter Integration**: MCP/CLI integration for live UI element inspection
- **End-to-End Automation**: Hybrid testing pipeline with AI smoke tests
- **Token Optimization**: Pre-processing reduces AI API usage by up to 80%
- **Professional QA Engine**: Comprehensive test reporting and coverage analysis

## 📝 License

See LICENSE file for details.
