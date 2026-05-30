"""Professional QA workflow engine with AI-optimized automation."""
import asyncio
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
import json

from .ai_spec import AISpec, TestCase, Priority, TestType
from .playwright_automation import SmartQAEngine, BrowserType, TestResult, TestStatus
from .parser import LocalSRSParser

logger = logging.getLogger(__name__)


class QAWorkflowConfig:
    """Configuration for QA workflow execution."""
    
    def __init__(
        self,
        browser_type: BrowserType = BrowserType.CHROMIUM,
        headless: bool = True,
        parallel_tests: int = 1,
        screenshot_on_failure: bool = True,
        retry_failed_tests: int = 1,
        timeout_ms: int = 30000
    ):
        self.browser_type = browser_type
        self.headless = headless
        self.parallel_tests = parallel_tests
        self.screenshot_on_failure = screenshot_on_failure
        self.retry_failed_tests = retry_failed_tests
        self.timeout_ms = timeout_ms


class QAWorkflow:
    """
    Professional QA workflow engine that orchestrates the entire testing process.
    Integrates AI-optimized specs with intelligent test execution.
    """
    
    def __init__(self, config: Optional[QAWorkflowConfig] = None):
        """
        Initialize QA workflow engine.
        
        Args:
            config: Workflow configuration. Uses defaults if not provided.
        """
        self.config = config or QAWorkflowConfig()
        self.qa_engine: Optional[SmartQAEngine] = None
        self.ai_spec: Optional[AISpec] = None
        self.execution_history: List[Dict] = []
        
        logger.info("Initialized QA workflow engine")
    
    async def load_srs(self, pdf_path: str, optimize_tokens: bool = True) -> AISpec:
        """
        Load and convert SRS PDF to AI-optimized specification.
        
        Args:
            pdf_path: Path to SRS PDF file
            optimize_tokens: Whether to optimize for minimal token consumption
            
        Returns:
            AI-optimized specification
        """
        logger.info(f"Loading SRS from {pdf_path}")
        
        parser = LocalSRSParser(pdf_path)
        self.ai_spec = parser.to_ai_spec(optimize_tokens=optimize_tokens)
        
        logger.info(f"Loaded {self.ai_spec.total_requirements} requirements with {self.ai_spec.total_test_cases} test cases")
        return self.ai_spec
    
    async def load_ai_spec(self, spec_path: str) -> AISpec:
        """
        Load pre-existing AI-optimized specification.
        
        Args:
            spec_path: Path to AI spec JSON file
            
        Returns:
            AI-optimized specification
        """
        logger.info(f"Loading AI spec from {spec_path}")
        
        with open(spec_path, 'r') as f:
            spec_data = json.load(f)
        
        self.ai_spec = AISpec(**spec_data)
        logger.info(f"Loaded AI spec with {self.ai_spec.total_requirements} requirements")
        
        return self.ai_spec
    
    async def initialize_engine(self) -> None:
        """Initialize the QA automation engine."""
        if not self.qa_engine:
            self.qa_engine = SmartQAEngine(
                browser_type=self.config.browser_type,
                headless=self.config.headless
            )
            await self.qa_engine.initialize()
            logger.info("QA automation engine initialized")
    
    async def cleanup(self) -> None:
        """Cleanup QA engine resources."""
        if self.qa_engine:
            await self.qa_engine.cleanup()
            logger.info("QA automation engine cleaned up")
    
    async def run_critical_path_tests(self) -> List[TestResult]:
        """
        Run tests on the critical path (high priority requirements).
        
        Returns:
            Test results for critical path tests
        """
        if not self.ai_spec:
            raise ValueError("AI spec not loaded. Call load_srs() or load_ai_spec() first.")
        
        await self.initialize_engine()
        
        # Get critical requirements
        critical_reqs = self.ai_spec.get_critical_path()
        logger.info(f"Running critical path tests for {len(critical_reqs)} requirements")
        
        # Collect all test cases for critical requirements
        critical_tests = []
        for module in self.ai_spec.modules:
            for req in module.requirements:
                if req.req_id in critical_reqs:
                    critical_tests.extend(req.test_cases)
        
        results = await self.qa_engine.automation.execute_test_suite(critical_tests)
        
        # Record execution
        self._record_execution("critical_path", results)
        
        return results
    
    async def run_smoke_tests(self) -> List[TestResult]:
        """
        Run smoke tests (quick sanity checks).
        
        Returns:
            Test results for smoke tests
        """
        if not self.ai_spec:
            raise ValueError("AI spec not loaded. Call load_srs() or load_ai_spec() first.")
        
        await self.initialize_engine()
        
        # Collect all smoke tests
        smoke_tests = []
        for module in self.ai_spec.modules:
            for req in module.requirements:
                for test_case in req.test_cases:
                    if test_case.test_type == TestType.SMOKE:
                        smoke_tests.append(test_case)
        
        logger.info(f"Running {len(smoke_tests)} smoke tests")
        results = await self.qa_engine.automation.execute_test_suite(smoke_tests)
        
        # Record execution
        self._record_execution("smoke", results)
        
        return results
    
    async def run_regression_tests(self, min_priority: Priority = Priority.MEDIUM) -> List[TestResult]:
        """
        Run regression tests based on priority level.
        
        Args:
            min_priority: Minimum priority level to include
            
        Returns:
            Test results for regression tests
        """
        if not self.ai_spec:
            raise ValueError("AI spec not loaded. Call load_srs() or load_ai_spec() first.")
        
        await self.initialize_engine()
        
        results = await self.qa_engine.run_priority_tests(
            self._get_all_test_cases(),
            min_priority=min_priority
        )
        
        # Record execution
        self._record_execution("regression", results)
        
        return results
    
    async def run_full_test_suite(self) -> List[TestResult]:
        """
        Run complete test suite for all requirements.
        
        Returns:
            Test results for all tests
        """
        if not self.ai_spec:
            raise ValueError("AI spec not loaded. Call load_srs() or load_ai_spec() first.")
        
        await self.initialize_engine()
        
        all_tests = self._get_all_test_cases()
        logger.info(f"Running full test suite with {len(all_tests)} tests")
        
        results = await self.qa_engine.automation.execute_test_suite(all_tests)
        
        # Record execution
        self._record_execution("full_suite", results)
        
        return results
    
    def _get_all_test_cases(self) -> List[TestCase]:
        """Get all test cases from the AI spec."""
        all_tests = []
        for module in self.ai_spec.modules:
            for req in module.requirements:
                all_tests.extend(req.test_cases)
        return all_tests
    
    def _record_execution(self, test_type: str, results: List[TestResult]) -> None:
        """Record test execution in history."""
        execution_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_type": test_type,
            "total_tests": len(results),
            "passed": sum(1 for r in results if r.status == TestStatus.PASSED),
            "failed": sum(1 for r in results if r.status == TestStatus.FAILED),
            "skipped": sum(1 for r in results if r.status == TestStatus.SKIPPED),
            "duration_ms": sum(r.duration_ms for r in results)
        }
        
        self.execution_history.append(execution_record)
        logger.info(f"Recorded execution: {execution_record}")
    
    def generate_execution_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive execution report.
        
        Returns:
            Execution report with statistics and history
        """
        if not self.execution_history:
            return {"message": "No test executions recorded"}
        
        total_executions = len(self.execution_history)
        total_tests = sum(e["total_tests"] for e in self.execution_history)
        total_passed = sum(e["passed"] for e in self.execution_history)
        total_failed = sum(e["failed"] for e in self.execution_history)
        
        return {
            "summary": {
                "total_executions": total_executions,
                "total_tests_run": total_tests,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "overall_pass_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
                "total_duration_ms": sum(e["duration_ms"] for e in self.execution_history)
            },
            "history": self.execution_history,
            "ai_spec_info": {
                "total_requirements": self.ai_spec.total_requirements if self.ai_spec else 0,
                "total_test_cases": self.ai_spec.total_test_cases if self.ai_spec else 0,
                "automation_coverage": self.ai_spec.automation_coverage if self.ai_spec else 0
            } if self.ai_spec else None
        }
    
    def export_report(self, output_path: str) -> None:
        """
        Export execution report to JSON file.
        
        Args:
            output_path: Path to save report
        """
        report = self.generate_execution_report()
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported execution report to {output_path}")
    
    async def run_intelligent_workflow(self) -> Dict[str, Any]:
        """
        Run intelligent QA workflow with adaptive test selection.
        
        This workflow:
        1. Runs smoke tests first
        2. If smoke tests pass, runs critical path tests
        3. If critical path passes, runs regression tests
        4. Generates comprehensive report
        
        Returns:
            Complete workflow results
        """
        logger.info("Starting intelligent QA workflow")
        
        workflow_results = {
            "smoke_tests": None,
            "critical_path": None,
            "regression": None,
            "final_status": "unknown"
        }
        
        try:
            # Phase 1: Smoke tests
            logger.info("Phase 1: Running smoke tests")
            smoke_results = await self.run_smoke_tests()
            workflow_results["smoke_tests"] = self.qa_engine.generate_test_report(smoke_results)
            
            smoke_passed = workflow_results["smoke_tests"]["summary"]["passed"] == workflow_results["smoke_tests"]["summary"]["total"]
            
            if not smoke_passed:
                logger.error("Smoke tests failed. Stopping workflow.")
                workflow_results["final_status"] = "failed_smoke"
                return workflow_results
            
            # Phase 2: Critical path tests
            logger.info("Phase 2: Running critical path tests")
            critical_results = await self.run_critical_path_tests()
            workflow_results["critical_path"] = self.qa_engine.generate_test_report(critical_results)
            
            critical_passed = workflow_results["critical_path"]["summary"]["passed"] == workflow_results["critical_path"]["summary"]["total"]
            
            if not critical_passed:
                logger.warning("Critical path tests had failures. Continuing with caution.")
                workflow_results["final_status"] = "partial_success"
            else:
                # Phase 3: Regression tests
                logger.info("Phase 3: Running regression tests")
                regression_results = await self.run_regression_tests()
                workflow_results["regression"] = self.qa_engine.generate_test_report(regression_results)
                
                regression_passed = workflow_results["regression"]["summary"]["pass_rate"] >= 80
                
                if regression_passed:
                    workflow_results["final_status"] = "success"
                else:
                    workflow_results["final_status"] = "regression_issues"
        
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            workflow_results["final_status"] = "error"
            workflow_results["error"] = str(e)
        
        finally:
            await self.cleanup()
        
        logger.info(f"Intelligent workflow completed with status: {workflow_results['final_status']}")
        return workflow_results


async def run_qa_workflow(pdf_path: str, output_dir: str = "qa_reports") -> Dict[str, Any]:
    """
    Convenience function to run complete QA workflow.
    
    Args:
        pdf_path: Path to SRS PDF file
        output_dir: Directory to save reports
        
    Returns:
        Complete workflow results
    """
    workflow = QAWorkflow()
    
    try:
        # Load SRS
        await workflow.load_srs(pdf_path)
        
        # Save AI spec for reference
        spec_output = Path(output_dir) / "ai_spec.json"
        spec_output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(spec_output, 'w') as f:
            json.dump(workflow.ai_spec.model_dump(), f, indent=2, ensure_ascii=False)
        
        # Run intelligent workflow
        results = await workflow.run_intelligent_workflow()
        
        # Export reports
        workflow.export_report(Path(output_dir) / "execution_report.json")
        
        return results
        
    except Exception as e:
        logger.error(f"QA workflow failed: {e}")
        raise
    finally:
        await workflow.cleanup()
