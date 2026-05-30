"""Example: Complete QA workflow with AI-optimized specs."""
import asyncio
from core import QAWorkflow, QAWorkflowConfig, BrowserType

async def run_qa_workflow_example():
    """Example of running complete QA workflow."""
    
    # Create workflow configuration
    config = QAWorkflowConfig(
        browser_type=BrowserType.CHROMIUM,
        headless=True,
        parallel_tests=1,
        screenshot_on_failure=True,
        retry_failed_tests=1
    )
    
    # Initialize workflow
    workflow = QAWorkflow(config)
    
    try:
        # Load SRS and convert to AI spec
        print("Loading SRS PDF...")
        await workflow.load_srs("srs_test.pdf", optimize_tokens=True)
        
        # Display spec information
        print(f"\n=== AI Spec Information ===")
        print(f"Project: {workflow.ai_spec.project_name}")
        print(f"Requirements: {workflow.ai_spec.total_requirements}")
        print(f"Test Cases: {workflow.ai_spec.total_test_cases}")
        print(f"Automation Coverage: {workflow.ai_spec.automation_coverage:.1f}%")
        
        # Get token estimate
        token_estimate = workflow.ai_spec.get_token_estimate()
        print(f"\n=== Token Optimization ===")
        print(f"Estimated Tokens: {token_estimate['estimated_tokens']}")
        print(f"Compression Ratio: {workflow.ai_spec.compression_ratio or 'N/A'}")
        
        # Run smoke tests
        print("\n=== Running Smoke Tests ===")
        smoke_results = await workflow.run_smoke_tests()
        smoke_report = workflow.qa_engine.generate_test_report(smoke_results)
        print(f"Smoke Tests: {smoke_report['summary']['passed']}/{smoke_report['summary']['total']} passed")
        
        # Run critical path tests
        print("\n=== Running Critical Path Tests ===")
        critical_results = await workflow.run_critical_path_tests()
        critical_report = workflow.qa_engine.generate_test_report(critical_results)
        print(f"Critical Tests: {critical_report['summary']['passed']}/{critical_report['summary']['total']} passed")
        
        # Generate execution report
        print("\n=== Generating Execution Report ===")
        report = workflow.generate_execution_report()
        print(f"Total Executions: {report['summary']['total_executions']}")
        print(f"Total Tests Run: {report['summary']['total_tests_run']}")
        print(f"Overall Pass Rate: {report['summary']['overall_pass_rate']:.1f}%")
        
        # Export report
        workflow.export_report("output/qa_execution_report.json")
        print("Report exported to output/qa_execution_report.json")
        
    except Exception as e:
        print(f"Workflow error: {e}")
        raise
    finally:
        # Cleanup
        await workflow.cleanup()
        print("\nWorkflow completed and cleaned up")


if __name__ == "__main__":
    asyncio.run(run_qa_workflow_example())
