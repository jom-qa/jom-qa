"""Example: Playwright automation for QA testing."""
import asyncio
from core import (
    PlaywrightAutomation,
    TestCase,
    TestStep,
    ActionType,
    SelectorType,
    BrowserType
)

async def run_playwright_example():
    """Example of using Playwright automation for testing."""
    
    # Initialize automation engine
    automation = PlaywrightAutomation(
        browser_type=BrowserType.CHROMIUM,
        headless=True,
        screenshot_dir="screenshots"
    )
    
    try:
        # Start browser
        await automation.start()
        print("Browser started successfully")
        
        # Create a sample test case
        test_case = TestCase(
            test_id="TC-LOGIN-001",
            name="User Login Test",
            description="Test user login functionality",
            steps=[
                TestStep(
                    action=ActionType.NAVIGATE,
                    selector="",
                    value="https://example.com/login",
                    description="Navigate to login page"
                ),
                TestStep(
                    action=ActionType.FILL,
                    selector="#email",
                    selector_type=SelectorType.CSS,
                    value="test@example.com",
                    description="Enter email address"
                ),
                TestStep(
                    action=ActionType.FILL,
                    selector="#password",
                    selector_type=SelectorType.CSS,
                    value="password123",
                    description="Enter password"
                ),
                TestStep(
                    action=ActionType.CLICK,
                    selector="button[type='submit']",
                    selector_type=SelectorType.CSS,
                    description="Click login button"
                ),
                TestStep(
                    action=ActionType.ASSERT,
                    selector=".welcome-message",
                    selector_type=SelectorType.CSS,
                    description="Verify welcome message appears"
                ),
                TestStep(
                    action=ActionType.SCREENSHOT,
                    selector="",
                    value="login_success",
                    description="Take screenshot after successful login"
                )
            ]
        )
        
        # Execute test case
        print(f"Executing test case: {test_case.test_id}")
        result = await automation.execute_test_case(test_case)
        
        print(f"\n=== Test Result ===")
        print(f"Test ID: {result.test_id}")
        print(f"Status: {result.status}")
        print(f"Duration: {result.duration_ms}ms")
        print(f"Steps Completed: {result.steps_completed}/{result.steps_total}")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        # Generate Playwright script
        print("\n=== Generated Playwright Script ===")
        script = automation.generate_playwright_script(test_case)
        print(script)
        
    finally:
        # Cleanup
        await automation.stop()
        print("\nBrowser stopped successfully")


if __name__ == "__main__":
    asyncio.run(run_playwright_example())
