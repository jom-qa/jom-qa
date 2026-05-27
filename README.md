# jom-QA
The core AI-powered QA automation engine for jom-QA. Parses SRS PDF documentation, generates native Flutter and Web integration tests, and orchestrates automated execution.

## 📂 Project Structure

```text
jom-qa-core/
│
├── core/
│   ├── __init__.py
│   └── parser.py               # Local SRS PDF to Structural JSON parser
│
├── reporters/
│   ├── __init__.py
│   └── base_reporter.py  # Abstract interface for bug reporting adapters
│
├── srs_test.pdf                # Generated sample SRS document
├── run_test_parser.py          # Quick playground execution script
├── requirements.txt
└── .gitignore
