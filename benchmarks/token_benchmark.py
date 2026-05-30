"""Benchmarking script to compare token usage between JSON and .spec formats."""
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import LocalSRSParser
from core.spec_format import SpecGenerator, calculate_spec_token_count


def calculate_json_token_count(json_data: dict) -> dict:
    """Calculate token count for JSON data."""
    json_str = json.dumps(json_data, indent=2)
    char_count = len(json_str)
    estimated_tokens = char_count // 4
    
    return {
        "total_characters": char_count,
        "estimated_tokens": estimated_tokens,
        "format": "json"
    }


def run_benchmark(pdf_path: str = "srs_test.pdf") -> dict:
    """
    Run comprehensive benchmark comparing JSON vs .spec formats.
    
    Args:
        pdf_path: Path to SRS PDF file
        
    Returns:
        Benchmark results
    """
    print("=" * 60)
    print("jom-qa Token Usage Benchmark")
    print("=" * 60)
    print(f"PDF Source: {pdf_path}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    # Parse PDF and generate AI spec
    print("Step 1: Parsing PDF and generating AI specification...")
    parser = LocalSRSParser(pdf_path)
    ai_spec = parser.to_ai_spec(optimize_tokens=True, target_tokens=4000)
    
    print(f"  - Requirements: {ai_spec.total_requirements}")
    print(f"  - Test Cases: {ai_spec.total_test_cases}")
    print(f"  - Modules: {len(ai_spec.modules)}")
    print()
    
    # Generate JSON format
    print("Step 2: Generating JSON format...")
    json_data = ai_spec.model_dump()
    json_str = json.dumps(json_data, indent=2)
    json_stats = calculate_json_token_count(json_data)
    print(f"  - Characters: {json_stats['total_characters']:,}")
    print(f"  - Estimated Tokens: {json_stats['estimated_tokens']:,}")
    print()
    
    # Generate .spec format
    print("Step 3: Generating .spec format...")
    spec_generator = SpecGenerator(strict=True)
    spec_content = spec_generator.generate(ai_spec)
    spec_stats = calculate_spec_token_count(spec_content)
    print(f"  - Characters: {spec_stats['total_characters']:,}")
    print(f"  - Lines: {spec_stats['total_lines']:,}")
    print(f"  - Estimated Tokens: {spec_stats['estimated_tokens']:,}")
    print()
    
    # Calculate savings
    print("Step 4: Calculating token savings...")
    json_tokens = json_stats['estimated_tokens']
    spec_tokens = spec_stats['estimated_tokens']
    token_savings = json_tokens - spec_tokens
    savings_percentage = (token_savings / json_tokens * 100) if json_tokens > 0 else 0
    
    print(f"  - JSON Tokens: {json_tokens:,}")
    print(f"  - .spec Tokens: {spec_tokens:,}")
    print(f"  - Token Savings: {token_savings:,} ({savings_percentage:.1f}%)")
    print()
    
    # Calculate compression ratio
    compression_ratio = spec_tokens / json_tokens if json_tokens > 0 else 0
    print(f"  - Compression Ratio: {compression_ratio:.2f}x")
    print()
    
    # Save sample files for comparison
    print("Step 5: Saving sample files...")
    output_dir = Path("benchmarks/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_path = output_dir / "benchmark_ai_spec.json"
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    print(f"  - JSON saved to: {json_path}")
    
    # Save .spec
    spec_path = output_dir / "benchmark_ai_spec.spec"
    spec_generator.save(ai_spec, str(spec_path))
    print(f"  - .spec saved to: {spec_path}")
    print()
    
    # Generate benchmark report
    benchmark_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "pdf_source": pdf_path,
        "ai_spec": {
            "total_requirements": ai_spec.total_requirements,
            "total_test_cases": ai_spec.total_test_cases,
            "modules": len(ai_spec.modules)
        },
        "json_format": {
            "characters": json_stats['total_characters'],
            "estimated_tokens": json_stats['estimated_tokens']
        },
        "spec_format": {
            "characters": spec_stats['total_characters'],
            "lines": spec_stats['total_lines'],
            "estimated_tokens": spec_stats['estimated_tokens']
        },
        "savings": {
            "token_savings": token_savings,
            "savings_percentage": savings_percentage,
            "compression_ratio": compression_ratio
        }
    }
    
    # Save benchmark report
    report_path = output_dir / "benchmark_report.json"
    with open(report_path, 'w') as f:
        json.dump(benchmark_results, f, indent=2)
    print(f"  - Benchmark report saved to: {report_path}")
    print()
    
    # Summary
    print("=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"Token Reduction: {savings_percentage:.1f}%")
    print(f"Compression Ratio: {compression_ratio:.2f}x")
    print(f"Format: .spec is {savings_percentage:.1f}% more efficient than JSON")
    print("=" * 60)
    
    return benchmark_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark token usage between JSON and .spec formats")
    parser.add_argument("--pdf", default="srs_test.pdf", help="Path to SRS PDF file")
    
    args = parser.parse_args()
    
    try:
        results = run_benchmark(args.pdf)
        print("\n✅ Benchmark completed successfully!")
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        sys.exit(1)
