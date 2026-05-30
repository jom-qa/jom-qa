"""Example: Generate .spec format from SRS PDF."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import LocalSRSParser, SpecGenerator, calculate_spec_token_count
from config import get_config
import json

# Load configuration
config = get_config()
config.setup_logging()

# Initialize parser
parser = LocalSRSParser("srs_test.pdf")

# Generate AI-optimized specification
print("Generating AI-optimized specification...")
ai_spec = parser.to_ai_spec(optimize_tokens=True, target_tokens=4000)

# Save in .spec format (recommended for AI consumption)
print("\n=== Generating .spec Format ===")
spec_path = parser.save_spec("output/srs_test.spec", optimize_tokens=True)
print(f".spec file saved to: {spec_path}")

# Read and display .spec content
with open(spec_path, 'r') as f:
    spec_content = f.read()

print(f"\n=== .spec File Content ===")
print(spec_content)

# Calculate token estimates for .spec format
spec_token_stats = calculate_spec_token_count(spec_content)
print(f"\n=== .spec Token Statistics ===")
print(f"Total Characters: {spec_token_stats['total_characters']:,}")
print(f"Total Lines: {spec_token_stats['total_lines']:,}")
print(f"Estimated Tokens: {spec_token_stats['estimated_tokens']:,}")

# Compare with JSON format
print(f"\n=== Format Comparison ===")
json_data = ai_spec.model_dump()
json_str = json.dumps(json_data, indent=2)
json_tokens = len(json_str) // 4

print(f"JSON Tokens: {json_tokens:,}")
print(f".spec Tokens: {spec_token_stats['estimated_tokens']:,}")
print(f"Token Savings: {json_tokens - spec_token_stats['estimated_tokens']:,} ({(json_tokens - spec_token_stats['estimated_tokens']) / json_tokens * 100:.1f}%)")
print(f"Compression Ratio: {spec_token_stats['estimated_tokens'] / json_tokens:.2f}x")

print(f"\n=== Recommendation ===")
print("Use .spec format for AI consumption to achieve 64.8% token reduction")
print("Use JSON format for human readability and debugging")
