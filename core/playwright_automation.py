"""Playwright integration for professional QA automation."""
import asyncio
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import json

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Locator
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from .ai_spec import TestCase, TestStep, ActionType, SelectorType, Priority

logger = logging.getLogger(__name__)


class BrowserType(str, Enum):
    """Supported browser types."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    """Result of a test execution."""
    test_id: str
    status: TestStatus
    duration_ms: int
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    steps_completed: int = 0
    steps_total: int = 0


class PlaywrightAutomation:
    """
    Professional QA automation engine using Playwright.
    Provides intelligent test execution with AI-enhanced capabilities.
    """
    
    def __init__(self, 
                 browser_type: BrowserType = BrowserType.CHROMIUM,
                 headless: bool = True,
                 screenshot_dir: str = "screenshots",
                 timeout: int = 30000):
        """
        Initialize Playwright automation engine.
        
        Args:
            browser_type: Browser to use for testing
            headless: Whether to run browser in headless mode
            screenshot_dir: Directory to save screenshots
            timeout: Default timeout in milliseconds
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is not installed. Install it with: pip install playwright && playwright install"
            )
        
        self.browser_type = browser_type
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir)
        self.timeout = timeout
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Create screenshot directory
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized Playwright automation with {browser_type} browser")
    
    async def start(self) -> None:
        """Start the browser and create context."""
        self.playwright = await async_playwright().start()
        
        browser_map = {
            BrowserType.CHROMIUM: self.playwright.chromium,
            BrowserType.FIREFOX: self.playwright.firefox,
            BrowserType.WEBKIT: self.playwright.webkit
        }
        
        self.browser = await browser_map[self.browser_type].launch(headless=self.headless)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        self.page = await self.context.new_page()
        
        logger.info(f"Started {self.browser_type} browser (headless={self.headless})")
    
    async def stop(self) -> None:
        """Stop the browser and cleanup."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        logger.info("Stopped browser and cleaned up resources")
    
    def _build_selector(self, step: TestStep) -> str:
        """
        Build Playwright selector from test step.
        
        Args:
            step: Test step with selector information
            
        Returns:
            Playwright selector string
        """
        if not step.selector:
            return ""
        
        selector_map = {
            SelectorType.CSS: step.selector,
            SelectorType.XPATH: f"xpath={step.selector}",
            SelectorType.TEXT: f"text={step.selector}",
            SelectorType.ROLE: f"role={step.selector}",
            SelectorType.LABEL: f"label={step.selector}",
            SelectorType.PLACEHOLDER: f"placeholder={step.selector}",
            SelectorType.ALT: f"alt={step.selector}"
        }
        
        return selector_map.get(step.selector_type, step.selector)
    
    async def _execute_step(self, step: TestStep) -> bool:
        """
        Execute a single test step.
        
        Args:
            step: Test step to execute
            
        Returns:
            True if step executed successfully, False otherwise
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        selector = self._build_selector(step)
        
        try:
            logger.debug(f"Executing step: {step.action} on {selector}")
            
            if step.action == ActionType.NAVIGATE:
                await self.page.goto(step.value, timeout=step.timeout or self.timeout)
            
            elif step.action == ActionType.CLICK:
                if selector:
                    await self.page.click(selector, timeout=step.timeout or self.timeout)
            
            elif step.action == ActionType.FILL:
                if selector and step.value:
                    await self.page.fill(selector, step.value, timeout=step.timeout or self.timeout)
            
            elif step.action == ActionType.SELECT:
                if selector and step.value:
                    await self.page.select_option(selector, step.value, timeout=step.timeout or self.timeout)
            
            elif step.action == ActionType.HOVER:
                if selector:
                    await self.page.hover(selector, timeout=step.timeout or self.timeout)
            
            elif step.action == ActionType.SCROLL:
                if step.value:
                    await self.page.evaluate(f"window.scrollBy(0, {step.value})")
                else:
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            elif step.action == ActionType.WAIT:
                await self.page.wait_for_timeout(step.value or 1000)
            
            elif step.action == ActionType.ASSERT:
                if selector:
                    await self.page.wait_for_selector(selector, timeout=step.timeout or self.timeout)
                elif step.value:
                    # Assert text is visible on page
                    await self.page.wait_for_selector(f"text={step.value}", timeout=step.timeout or self.timeout)
            
            elif step.action == ActionType.SCREENSHOT:
                screenshot_path = self.screenshot_dir / f"{step.description.replace(' ', '_')}.png"
                await self.page.screenshot(path=str(screenshot_path))
                logger.info(f"Screenshot saved to {screenshot_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            if not step.optional:
                # Take screenshot on failure
                screenshot_path = self.screenshot_dir / f"error_{step.description.replace(' ', '_')}.png"
                await self.page.screenshot(path=str(screenshot_path))
                logger.info(f"Error screenshot saved to {screenshot_path}")
                return False
            return True
    
    async def execute_test_case(self, test_case: TestCase) -> TestResult:
        """
        Execute a complete test case.
        
        Args:
            test_case: Test case to execute
            
        Returns:
            Test result with status and details
        """
        import time
        
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        result = TestResult(
            test_id=test_case.test_id,
            status=TestStatus.RUNNING,
            duration_ms=0,
            steps_total=len(test_case.steps)
        )
        
        logger.info(f"Executing test case: {test_case.test_id} - {test_case.name}")
        start_time = time.time()
        
        try:
            for step in test_case.steps:
                success = await self._execute_step(step)
                if success:
                    result.steps_completed += 1
                else:
                    result.status = TestStatus.FAILED
                    result.error_message = f"Step failed: {step.description}"
                    break
            
            if result.status == TestStatus.RUNNING:
                result.status = TestStatus.PASSED
                logger.info(f"Test case {test_case.test_id} passed")
            else:
                logger.error(f"Test case {test_case.test_id} failed: {result.error_message}")
                
        except Exception as e:
            result.status = TestStatus.FAILED
            result.error_message = str(e)
            logger.error(f"Test case execution error: {e}")
        
        result.duration_ms = int((time.time() - start_time) * 1000)
        return result
    
    async def execute_test_suite(self, test_cases: List[TestCase]) -> List[TestResult]:
        """
        Execute multiple test cases.
        
        Args:
            test_cases: List of test cases to execute
            
        Returns:
            List of test results
        """
        results = []
        
        for test_case in test_cases:
            if not test_case.automated:
                logger.info(f"Skipping non-automated test: {test_case.test_id}")
                results.append(TestResult(
                    test_id=test_case.test_id,
                    status=TestStatus.SKIPPED,
                    duration_ms=0
                ))
                continue
            
            result = await self.execute_test_case(test_case)
            results.append(result)
        
        return results
    
    def generate_playwright_script(self, test_case: TestCase) -> str:
        """
        Generate Playwright Python script from test case.
        
        Args:
            test_case: Test case to convert to script
            
        Returns:
            Playwright Python script
        """
        script_lines = [
            "import asyncio",
            "from playwright.async_api import async_playwright",
            "",
            "async def run_test():",
            "    async with async_playwright() as p:",
            "        browser = await p.chromium.launch(headless=True)",
            "        page = await browser.new_page()",
            ""
        ]
        
        for step in test_case.steps:
            selector = self._build_selector(step)
            indent = "        "
            
            if step.action == ActionType.NAVIGATE:
                script_lines.append(f'{indent}await page.goto("{step.value}")')
            
            elif step.action == ActionType.CLICK:
                script_lines.append(f'{indent}await page.click("{selector}")')
            
            elif step.action == ActionType.FILL:
                script_lines.append(f'{indent}await page.fill("{selector}", "{step.value}")')
            
            elif step.action == ActionType.SELECT:
                script_lines.append(f'{indent}await page.select_option("{selector}", "{step.value}")')
            
            elif step.action == ActionType.HOVER:
                script_lines.append(f'{indent}await page.hover("{selector}")')
            
            elif step.action == ActionType.SCROLL:
                if step.value:
                    script_lines.append(f'{indent}await page.evaluate("window.scrollBy(0, {step.value})")')
                else:
                    script_lines.append(f'{indent}await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")')
            
            elif step.action == ActionType.WAIT:
                script_lines.append(f'{indent}await page.wait_for_timeout({step.value or 1000})')
            
            elif step.action == ActionType.ASSERT:
                if selector:
                    script_lines.append(f'{indent}await page.wait_for_selector("{selector}")')
                elif step.value:
                    script_lines.append(f'{indent}await page.wait_for_selector("text={step.value}")')
            
            elif step.action == ActionType.SCREENSHOT:
                script_lines.append(f'{indent}await page.screenshot(path="screenshots/{step.description.replace(" ", "_")}.png")')
        
        script_lines.extend([
            "",
            "        await browser.close()",
            "",
            "asyncio.run(run_test())"
        ])
        
        return "\n".join(script_lines)
    
    async def intelligent_element_detection(self, description: str) -> Optional[Dict[str, Any]]:
        """
        Intelligently detect UI elements based on natural language description.
        This is a placeholder for AI-enhanced element detection.
        
        Args:
            description: Natural language description of element
            
        Returns:
            Dictionary with element information (selector, type, etc.)
        """
        # This would be enhanced with AI in the future
        # For now, return a basic implementation
        
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        # Get all interactive elements
        elements = await self.page.query_selector_all("button, input, select, a, [role='button']")
        
        # Simple keyword matching (would be replaced with AI)
        keywords = description.lower().split()
        
        for element in elements:
            text = await element.text_content()
            if text and any(keyword in text.lower() for keyword in keywords):
                return {
                    "selector": f"text={text}",
                    "type": "text",
                    "text": text
                }
        
        return None


class SmartQAEngine:
    """
    Intelligent QA engine that combines AI-optimized specs with Playwright automation.
    Provides professional-grade testing capabilities with minimal AI token consumption.
    """
    
    def __init__(self, browser_type: BrowserType = BrowserType.CHROMIUM, headless: bool = True):
        """
        Initialize smart QA engine.
        
        Args:
            browser_type: Browser to use for testing
            headless: Whether to run browser in headless mode
        """
        self.automation = PlaywrightAutomation(browser_type=browser_type, headless=headless)
        self.test_results: List[TestResult] = []
    
    async def initialize(self) -> None:
        """Initialize the QA engine."""
        await self.automation.start()
    
    async def cleanup(self) -> None:
        """Cleanup QA engine resources."""
        await self.automation.stop()
    
    async def run_priority_tests(self, test_cases: List[TestCase], min_priority: Priority = Priority.HIGH) -> List[TestResult]:
        """
        Run tests based on priority level.
        
        Args:
            test_cases: All available test cases
            min_priority: Minimum priority level to run
            
        Returns:
            Test results for executed tests
        """
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3
        }
        
        min_order = priority_order[min_priority]
        filtered_tests = [
            tc for tc in test_cases 
            if priority_order.get(tc.priority, 999) <= min_order
        ]
        
        logger.info(f"Running {len(filtered_tests)} tests with priority >= {min_priority}")
        return await self.automation.execute_test_suite(filtered_tests)
    
    async def run_smoke_tests(self, test_cases: List[TestCase]) -> List[TestResult]:
        """
        Run smoke tests (quick sanity checks).
        
        Args:
            test_cases: All available test cases
            
        Returns:
            Test results for smoke tests
        """
        smoke_tests = [tc for tc in test_cases if tc.test_type.value == "smoke"]
        logger.info(f"Running {len(smoke_tests)} smoke tests")
        return await self.automation.execute_test_suite(smoke_tests)
    
    def generate_test_report(self, results: List[TestResult]) -> Dict[str, Any]:
        """
        Generate comprehensive test report.
        
        Args:
            results: Test execution results
            
        Returns:
            Test report dictionary
        """
        total = len(results)
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        
        total_duration = sum(r.duration_ms for r in results)
        
        return {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "pass_rate": (passed / total * 100) if total > 0 else 0,
                "total_duration_ms": total_duration
            },
            "results": [
                {
                    "test_id": r.test_id,
                    "status": r.status.value,
                    "duration_ms": r.duration_ms,
                    "error": r.error_message,
                    "steps_completed": r.steps_completed,
                    "steps_total": r.steps_total
                }
                for r in results
            ]
        }
