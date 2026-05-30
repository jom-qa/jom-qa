"""AI-optimized specification format for professional QA automation."""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime
import json


class Priority(str, Enum):
    """Requirement priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestType(str, Enum):
    """Types of automated tests."""
    SMOKE = "smoke"
    REGRESSION = "regression"
    INTEGRATION = "integration"
    E2E = "e2e"
    SECURITY = "security"
    PERFORMANCE = "performance"


class ActionType(str, Enum):
    """Types of user actions for test automation."""
    NAVIGATE = "navigate"
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    HOVER = "hover"
    SCROLL = "scroll"
    WAIT = "wait"
    ASSERT = "assert"
    SCREENSHOT = "screenshot"


class SelectorType(str, Enum):
    """Types of element selectors."""
    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    ROLE = "role"
    LABEL = "label"
    PLACEHOLDER = "placeholder"
    ALT = "alt"


class TestStep(BaseModel):
    """Individual test step for automation."""
    action: ActionType = Field(..., description="Action to perform")
    selector: Optional[str] = Field(None, description="Element selector")
    selector_type: SelectorType = Field(default=SelectorType.CSS, description="Type of selector")
    value: Optional[str] = Field(None, description="Value to input or expected result")
    description: str = Field(..., description="Human-readable description")
    timeout: Optional[int] = Field(default=5000, description="Timeout in milliseconds")
    optional: bool = Field(default=False, description="Whether step is optional")


class TestCase(BaseModel):
    """AI-optimized test case specification."""
    test_id: str = Field(..., description="Unique test identifier")
    name: str = Field(..., description="Test case name")
    description: str = Field(..., description="Detailed test description")
    test_type: TestType = Field(default=TestType.REGRESSION, description="Type of test")
    priority: Priority = Field(default=Priority.MEDIUM, description="Test priority")
    preconditions: List[str] = Field(default_factory=list, description="Preconditions for test")
    steps: List[TestStep] = Field(default_factory=list, description="Test execution steps")
    expected_result: str = Field(..., description="Expected test outcome")
    tags: List[str] = Field(default_factory=list, description="Test tags for filtering")
    automated: bool = Field(default=True, description="Whether test is automated")
    playwright_script: Optional[str] = Field(None, description="Generated Playwright script")
    
    @validator('test_id')
    def validate_test_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Test ID cannot be empty")
        return v.strip()


class RequirementSpec(BaseModel):
    """AI-optimized requirement specification."""
    req_id: str = Field(..., description="Unique requirement identifier")
    title: str = Field(..., description="Requirement title")
    description: str = Field(..., description="Detailed requirement description")
    priority: Priority = Field(default=Priority.MEDIUM, description="Requirement priority")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Acceptance criteria")
    test_cases: List[TestCase] = Field(default_factory=list, description="Associated test cases")
    dependencies: List[str] = Field(default_factory=list, description="Dependent requirement IDs")
    risk_level: str = Field(default="medium", description="Risk level (low/medium/high)")
    complexity: str = Field(default="medium", description="Implementation complexity")
    estimated_effort: Optional[str] = Field(None, description="Estimated effort for implementation")
    
    @validator('req_id')
    def validate_req_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Requirement ID cannot be empty")
        return v.strip()


class ModuleSpec(BaseModel):
    """AI-optimized module specification."""
    module_id: str = Field(..., description="Unique module identifier")
    module_name: str = Field(..., description="Module name")
    description: str = Field(default="", description="Module description")
    requirements: List[RequirementSpec] = Field(default_factory=list, description="Module requirements")
    dependencies: List[str] = Field(default_factory=list, description="Dependent module IDs")
    test_coverage: float = Field(default=0.0, description="Test coverage percentage")
    risk_score: float = Field(default=0.0, description="Overall module risk score")
    
    @validator('module_id')
    def validate_module_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Module ID cannot be empty")
        return v.strip()


class AISpec(BaseModel):
    """
    AI-optimized specification format.
    Designed for minimal AI token consumption while maximizing QA automation capabilities.
    """
    spec_version: str = Field(default="2.0", description="Specification format version")
    project_name: str = Field(..., description="Project name")
    project_description: str = Field(default="", description="Project description")
    modules: List[ModuleSpec] = Field(default_factory=list, description="Project modules")
    
    # Metadata for AI optimization
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Specification metadata")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Creation timestamp")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Last update timestamp")
    
    # AI optimization fields
    token_optimized: bool = Field(default=True, description="Whether spec is token-optimized")
    compression_ratio: Optional[float] = Field(None, description="Token compression ratio achieved")
    ai_model_target: str = Field(default="claude-3-haiku", description="Target AI model for processing")
    
    # Cross-references
    external_refs: Dict[str, str] = Field(default_factory=dict, description="External specification references")
    internal_refs: Dict[str, List[str]] = Field(default_factory=dict, description="Internal cross-references")
    
    # Quality metrics
    total_requirements: int = Field(default=0, description="Total requirement count")
    total_test_cases: int = Field(default=0, description="Total test case count")
    automation_coverage: float = Field(default=0.0, description="Test automation coverage percentage")
    
    def calculate_metrics(self) -> None:
        """Calculate quality metrics for the specification."""
        self.total_requirements = sum(len(mod.requirements) for mod in self.modules)
        self.total_test_cases = sum(
            len(req.test_cases) 
            for mod in self.modules 
            for req in mod.requirements
        )
        
        if self.total_requirements > 0:
            automated_tests = sum(
                len([tc for tc in req.test_cases if tc.automated])
                for mod in self.modules
                for req in mod.requirements
            )
            self.automation_coverage = (automated_tests / self.total_test_cases * 100) if self.total_test_cases > 0 else 0.0
    
    def get_token_estimate(self) -> Dict[str, int]:
        """
        Estimate token consumption for AI processing.
        
        Returns:
            Dictionary with token estimates for different components
        """
        spec_json = json.dumps(self.model_dump(), indent=2)
        char_count = len(spec_json)
        
        # Rough estimate: 1 token ≈ 4 characters
        total_tokens = char_count // 4
        
        return {
            "total_characters": char_count,
            "estimated_tokens": total_tokens,
            "modules": len(self.modules),
            "requirements": self.total_requirements,
            "test_cases": self.total_test_cases
        }
    
    def get_critical_path(self) -> List[str]:
        """
        Identify critical requirements based on priority and dependencies.
        
        Returns:
            List of critical requirement IDs in execution order
        """
        critical_reqs = []
        
        for module in self.modules:
            for req in module.requirements:
                if req.priority in [Priority.CRITICAL, Priority.HIGH]:
                    critical_reqs.append(req.req_id)
        
        return critical_reqs
    
    def generate_test_matrix(self) -> Dict[str, List[str]]:
        """
        Generate a test matrix for comprehensive coverage.
        
        Returns:
            Dictionary mapping test types to requirement IDs
        """
        test_matrix = {
            "smoke": [],
            "regression": [],
            "integration": [],
            "e2e": []
        }
        
        for module in self.modules:
            for req in module.requirements:
                for test_case in req.test_cases:
                    if test_case.test_type.value in test_matrix:
                        test_matrix[test_case.test_type.value].append(req.req_id)
        
        return test_matrix


class SpecConverter:
    """Converter from basic SRS format to AI-optimized spec format."""
    
    @staticmethod
    def from_basic_srs(basic_srs: Dict) -> AISpec:
        """
        Convert basic SRS format to AI-optimized spec.
        
        Args:
            basic_srs: Basic SRS dictionary from parser
            
        Returns:
            AI-optimized specification
        """
        ai_spec = AISpec(
            project_name=basic_srs.get("project_name", "Unknown Project"),
            metadata=basic_srs.get("metadata", {})
        )
        
        for module_data in basic_srs.get("modules", []):
            module_spec = ModuleSpec(
                module_id=module_data["module_name"].lower().replace(" ", "-"),
                module_name=module_data["module_name"],
                description=""
            )
            
            for req_data in module_data.get("requirements", []):
                priority_value = req_data.get("priority", "medium")
                # Handle None or invalid priority values
                if priority_value is None or priority_value == "":
                    priority_value = "medium"
                try:
                    priority = Priority(priority_value.lower())
                except (ValueError, AttributeError):
                    priority = Priority.MEDIUM
                
                req_spec = RequirementSpec(
                    req_id=req_data["req_id"],
                    title=req_data["title"],
                    description=req_data.get("description", ""),
                    priority=priority
                )
                
                # Generate basic test case from requirement
                test_case = TestCase(
                    test_id=f"TC-{req_data['req_id']}",
                    name=f"Test {req_data['title']}",
                    description=f"Automated test for {req_data['title']}",
                    test_type=TestType.REGRESSION,
                    priority=req_spec.priority,
                    expected_result=f"{req_data['title']} should work correctly",
                    automated=True
                )
                
                req_spec.test_cases.append(test_case)
                module_spec.requirements.append(req_spec)
            
            ai_spec.modules.append(module_spec)
        
        ai_spec.calculate_metrics()
        return ai_spec
    
    @staticmethod
    def optimize_for_tokens(spec: AISpec, target_tokens: int = 4000) -> AISpec:
        """
        Optimize specification for minimal token consumption.
        
        Args:
            spec: AI specification to optimize
            target_tokens: Target token limit
            
        Returns:
            Optimized specification
        """
        current_estimate = spec.get_token_estimate()["estimated_tokens"]
        
        if current_estimate <= target_tokens:
            return spec
        
        # Optimization strategies:
        # 1. Remove non-critical test cases
        # 2. Compress descriptions
        # 3. Remove optional metadata
        
        optimized = spec.model_copy()
        
        for module in optimized.modules:
            for req in module.requirements:
                # Keep only critical and high priority test cases
                req.test_cases = [
                    tc for tc in req.test_cases 
                    if tc.priority in [Priority.CRITICAL, Priority.HIGH]
                ]
                
                # Compress description
                if len(req.description) > 200:
                    req.description = req.description[:200] + "..."
        
        optimized.calculate_metrics()
        return optimized
