from core import LocalSRSParser, ParserConfig
from config import get_config
import json

# Load configuration
config = get_config()
config.setup_logging()

# Initialize parser with default configuration
parser = LocalSRSParser("srs_test.pdf")

# Option 1: Use the complete parsing pipeline
structured_json = parser.parse()

# Option 2: Save to JSON file
# output_path = parser.save_to_json("output/srs_parsed.json")

# Display the structured JSON output
print(json.dumps(structured_json, indent=2))

# Print metadata
print("\n=== Parsing Metadata ===")
print(f"Project: {structured_json.get('project_name')}")
print(f"Modules: {len(structured_json.get('modules', []))}")
print(f"Total Requirements: {sum(len(m.get('requirements', [])) for m in structured_json.get('modules', []))}")
if 'metadata' in structured_json:
    print(f"Parser Version: {structured_json['metadata'].get('parser_version')}")
    print(f"Lines Processed: {structured_json['metadata'].get('lines_processed')}")
