"""Unit tests for AI specification format."""
import pytest
from core.ai_spec import (
    AISpec,
    ModuleSpec,
    RequirementSpec,
    TestCase,
    TestStep,
    SpecConverter,
    Priority,
    TestType,
    ActionType,
    SelectorType
)


class TestAISpec:
    """Test AISpec model."""
    
    def test_ai_spec_creation(self):
        """Test creating AI specification."""
        spec = AISpec(
            project_name="Test Project",
            project_description="Test Description"
        )
        assert spec.project_name == "Test Project"
        assert spec.spec_version == "2.0"
        assert spec.token_optimized is True
    
    def test_calculate_metrics(self):
        """Test metrics calculation."""
        spec = AISpec(project_name="Test")
        
        module = ModuleSpec(
            module_id="auth",
            module_name="Authentication"
        )
        
        req = RequirementSpec(
            req_id="FR-001",
            title="User Login",
            description="Login functionality"
        )
        
        test_case = TestCase(
            test_id="TC-001",
            name="Login Test",
            description="Test login",
            expected_result="Success"
        )
        
        req.test_cases.append(test_case)
        module.requirements.append(req)
        spec.modules.append(module)
        
        spec.calculate_metrics()
        
        assert spec.total_requirements == 1
        assert spec.total_test_cases == 1
        assert spec.automation_coverage == 100.0


class TestTestCase:
    """Test TestCase model."""
    
    def test_test_case_creation(self):
        """Test creating test case."""
        step = TestStep(
            action=ActionType.CLICK,
            selector="#button",
            description="Click button"
        )
        
        test_case = TestCase(
            test_id="TC-001",
            name="Test",
            description="Test description",
            steps=[step],
            expected_result="Success"
        )
        
        assert test_case.test_id == "TC-001"
        assert len(test_case.steps) == 1
        assert test_case.automated is True


class TestSpecConverter:
    """Test SpecConverter functionality."""
    
    def test_from_basic_srs(self):
        """Test converting basic SRS to AI spec."""
        basic_srs = {
            "project_name": "Test Project",
            "modules": [
                {
                    "module_name": "Authentication",
                    "requirements": [
                        {
                            "req_id": "FR-001",
                            "title": "User Login",
                            "description": "Login functionality",
                            "priority": "high"
                        }
                    ]
                }
            ]
        }
        
        ai_spec = SpecConverter.from_basic_srs(basic_srs)
        
        assert ai_spec.project_name == "Test Project"
        assert len(ai_spec.modules) == 1
        assert ai_spec.modules[0].module_name == "Authentication"
        assert len(ai_spec.modules[0].requirements) == 1
        assert ai_spec.modules[0].requirements[0].req_id == "FR-001"
    
    def test_optimize_for_tokens(self):
        """Test token optimization."""
        basic_srs = {
            "project_name": "Test Project",
            "modules": [
                {
                    "module_name": "Auth",
                    "requirements": [
                        {
                            "req_id": "FR-001",
                            "title": "Login",
                            "description": "A" * 300,  # Long description
                            "priority": "low"
                        }
                    ]
                }
            ]
        }
        
        ai_spec = SpecConverter.from_basic_srs(basic_srs)
        original_tokens = ai_spec.get_token_estimate()["estimated_tokens"]
        
        optimized = SpecConverter.optimize_for_tokens(ai_spec, target_tokens=100)
        optimized_tokens = optimized.get_token_estimate()["estimated_tokens"]
        
        # Should reduce tokens by removing low priority items
        assert optimized_tokens <= original_tokens


class TestPriority:
    """Test Priority enum."""
    
    def test_priority_values(self):
        """Test priority enum values."""
        assert Priority.CRITICAL.value == "critical"
        assert Priority.HIGH.value == "high"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.LOW.value == "low"


class TestActionType:
    """Test ActionType enum."""
    
    def test_action_type_values(self):
        """Test action type enum values."""
        assert ActionType.NAVIGATE.value == "navigate"
        assert ActionType.CLICK.value == "click"
        assert ActionType.FILL.value == "fill"
        assert ActionType.ASSERT.value == "assert"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
