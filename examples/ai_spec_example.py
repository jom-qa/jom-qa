"""Example: Generate AI-optimized specification from SRS PDF."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import LocalSRSParser
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

# Display token estimates
token_estimate = ai_spec.get_token_estimate()
print("\n=== Token Optimization Results ===")
print(f"Total Characters: {token_estimate['total_characters']}")
print(f"Estimated Tokens: {token_estimate['estimated_tokens']}")
print(f"Modules: {token_estimate['modules']}")
print(f"Requirements: {token_estimate['requirements']}")
print(f"Test Cases: {token_estimate['test_cases']}")

# Display spec summary
print("\n=== Specification Summary ===")
print(f"Project: {ai_spec.project_name}")
print(f"Total Requirements: {ai_spec.total_requirements}")
print(f"Total Test Cases: {ai_spec.total_test_cases}")
print(f"Automation Coverage: {ai_spec.automation_coverage:.1f}%")

# Display critical path
critical_path = ai_spec.get_critical_path()
print(f"\nCritical Path Requirements: {len(critical_path)}")
for req_id in critical_path:
    print(f"  - {req_id}")

# Save AI spec to file
output_path = parser.save_ai_spec("output/ai_spec.json", optimize_tokens=True)
print(f"\nAI-optimized spec saved to: {output_path}")

# Display sample module structure
if ai_spec.modules:
    print("\n=== Sample Module Structure ===")
    module = ai_spec.modules[0]
    print(f"Module: {module.module_name}")
    print(f"Requirements: {len(module.requirements)}")
    if module.requirements:
        req = module.requirements[0]
        print(f"\nSample Requirement: {req.req_id}")
        print(f"  Title: {req.title}")
        print(f"  Priority: {req.priority}")
        print(f"  Test Cases: {len(req.test_cases)}")
        if req.test_cases:
            tc = req.test_cases[0]
            print(f"  Sample Test: {tc.test_id}")
            print(f"    Type: {tc.test_type}")
            print(f"    Automated: {tc.automated}")
