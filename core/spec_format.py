"""
jom-qa .spec file format specification and implementation.

The .spec format is a lightweight, AI-optimized specification format designed for:
- Minimal token consumption
- Easy AI understanding
- Strict structure validation
- Human readability
- Machine parsing efficiency

Format Specification:
- Lines are key-value pairs or section headers
- Sections start with ## SECTION_NAME
- Indentation denotes hierarchy
- Comments start with #
- Empty lines are ignored
- Strict typing with type hints
"""

import re
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .ai_spec import AISpec, ModuleSpec, RequirementSpec, TestCase, TestStep, Priority, TestType, ActionType

logger = logging.getLogger(__name__)


class SpecTokenType(str, Enum):
    """Token types for .spec format."""
    SECTION = "section"
    KEY_VALUE = "key_value"
    LIST_ITEM = "list_item"
    COMMENT = "comment"
    EMPTY = "empty"


@dataclass
class SpecToken:
    """Token in .spec format."""
    type: SpecTokenType
    key: Optional[str] = None
    value: Optional[str] = None
    indent: int = 0
    line_number: int = 0


class SpecParser:
    """Parser for .spec file format."""
    
    # Strict pattern matching for validation
    SECTION_PATTERN = re.compile(r'^##\s+([A-Z_]+)$')
    KEY_VALUE_PATTERN = re.compile(r'^([a-z_]+):\s*(.+)$')
    LIST_ITEM_PATTERN = re.compile(r'^-\s*(.+)$')
    COMMENT_PATTERN = re.compile(r'^#.*$')
    TYPE_HINT_PATTERN = re.compile(r'^([a-z_]+):\s*(.+)\s+<([a-z]+)>$')
    
    def __init__(self, strict: bool = True):
        """
        Initialize spec parser.
        
        Args:
            strict: Whether to enforce strict format validation
        """
        self.strict = strict
        self.tokens: List[SpecToken] = []
    
    def parse(self, content: str) -> List[SpecToken]:
        """
        Parse .spec content into tokens.
        
        Args:
            content: .spec file content
            
        Returns:
            List of parsed tokens
        """
        self.tokens = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                self.tokens.append(SpecToken(SpecTokenType.EMPTY, line_number=line_num))
                continue
            
            # Skip comments
            if self.COMMENT_PATTERN.match(stripped):
                self.tokens.append(SpecToken(SpecTokenType.COMMENT, line_number=line_num))
                continue
            
            # Match section headers
            section_match = self.SECTION_PATTERN.match(stripped)
            if section_match:
                self.tokens.append(SpecToken(
                    SpecTokenType.SECTION,
                    key=section_match.group(1),
                    line_number=line_num
                ))
                continue
            
            # Match key-value pairs with type hints
            type_hint_match = self.TYPE_HINT_PATTERN.match(stripped)
            if type_hint_match:
                self.tokens.append(SpecToken(
                    SpecTokenType.KEY_VALUE,
                    key=type_hint_match.group(1),
                    value=type_hint_match.group(2),
                    line_number=line_num
                ))
                continue
            
            # Match regular key-value pairs
            kv_match = self.KEY_VALUE_PATTERN.match(stripped)
            if kv_match:
                self.tokens.append(SpecToken(
                    SpecTokenType.KEY_VALUE,
                    key=kv_match.group(1),
                    value=kv_match.group(2),
                    line_number=line_num
                ))
                continue
            
            # Match list items
            list_match = self.LIST_ITEM_PATTERN.match(stripped)
            if list_match:
                self.tokens.append(SpecToken(
                    SpecTokenType.LIST_ITEM,
                    value=list_match.group(1),
                    line_number=line_num
                ))
                continue
            
            # Strict mode: raise error on unrecognized format
            if self.strict:
                raise ValueError(f"Line {line_num}: Invalid .spec format: '{stripped}'")
        
        return self.tokens
    
    def validate(self) -> bool:
        """
        Validate parsed tokens.
        
        Returns:
            True if valid, raises exception otherwise
        """
        # Check for required sections
        sections = [t.key for t in self.tokens if t.type == SpecTokenType.SECTION]
        required_sections = ['METADATA', 'MODULES']
        
        for section in required_sections:
            if section not in sections:
                raise ValueError(f"Missing required section: {section}")
        
        # Validate section order
        if sections.index('METADATA') > sections.index('MODULES'):
            raise ValueError("METADATA section must come before MODULES section")
        
        # Validate type hints in key-value pairs
        for token in self.tokens:
            if token.type == SpecTokenType.KEY_VALUE:
                if '<' in str(token.value) and '>' in str(token.value):
                    # Has type hint, validate it
                    type_hint_match = self.TYPE_HINT_PATTERN.match(f"{token.key}: {token.value}")
                    if not type_hint_match:
                        raise ValueError(f"Invalid type hint format at line {token.line_number}: {token.key}: {token.value}")
        
        return True


class SpecGenerator:
    """Generator for .spec file format from AI spec."""
    
    def __init__(self, strict: bool = True):
        """
        Initialize spec generator.
        
        Args:
            strict: Whether to generate strict format
        """
        self.strict = strict
    
    def generate(self, ai_spec: AISpec) -> str:
        """
        Generate .spec content from AI specification.
        
        Args:
            ai_spec: AI specification to convert
            
        Returns:
            .spec format content
        """
        lines = []
        
        # Header
        lines.append("# jom-qa Specification Format")
        lines.append("# Generated: " + datetime.utcnow().isoformat())
        lines.append("")
        
        # Metadata section
        lines.append("## METADATA")
        lines.append(f"spec_version: {ai_spec.spec_version} <str>")
        lines.append(f"project_name: {ai_spec.project_name} <str>")
        lines.append(f"project_description: {ai_spec.project_description} <str>")
        lines.append(f"token_optimized: {str(ai_spec.token_optimized).lower()} <bool>")
        lines.append(f"ai_model_target: {ai_spec.ai_model_target} <str>")
        lines.append(f"total_requirements: {ai_spec.total_requirements} <int>")
        lines.append(f"total_test_cases: {ai_spec.total_test_cases} <int>")
        lines.append(f"automation_coverage: {ai_spec.automation_coverage:.1f} <float>")
        lines.append("")
        
        # Modules section
        lines.append("## MODULES")
        for module in ai_spec.modules:
            lines.append(f"- module: {module.module_name} <str>")
            lines.append(f"  module_id: {module.module_id} <str>")
            lines.append(f"  requirements_count: {len(module.requirements)} <int>")
            
            # Requirements
            for req in module.requirements:
                lines.append(f"  - requirement: {req.req_id} <str>")
                lines.append(f"    title: {req.title} <str>")
                lines.append(f"    priority: {req.priority.value} <str>")
                lines.append(f"    test_cases_count: {len(req.test_cases)} <int>")
                
                # Test cases
                for tc in req.test_cases:
                    lines.append(f"    - test_case: {tc.test_id} <str>")
                    lines.append(f"      name: {tc.name} <str>")
                    lines.append(f"      type: {tc.test_type.value} <str>")
                    lines.append(f"      priority: {tc.priority.value} <str>")
                    lines.append(f"      automated: {str(tc.automated).lower()} <bool>")
                    lines.append(f"      steps_count: {len(tc.steps)} <int>")
            
            lines.append("")
        
        # Critical path section
        critical_path = ai_spec.get_critical_path()
        if critical_path:
            lines.append("## CRITICAL_PATH")
            for req_id in critical_path:
                lines.append(f"- {req_id} <str>")
            lines.append("")
        
        # Token estimation section
        token_estimate = ai_spec.get_token_estimate()
        lines.append("## TOKEN_ESTIMATE")
        lines.append(f"total_characters: {token_estimate['total_characters']} <int>")
        lines.append(f"estimated_tokens: {token_estimate['estimated_tokens']} <int>")
        lines.append(f"modules: {token_estimate['modules']} <int>")
        lines.append(f"requirements: {token_estimate['requirements']} <int>")
        lines.append(f"test_cases: {token_estimate['test_cases']} <int>")
        lines.append("")
        
        return "\n".join(lines)
    
    def save(self, ai_spec: AISpec, output_path: str) -> str:
        """
        Generate and save .spec file.
        
        Args:
            ai_spec: AI specification to convert
            output_path: Path to save .spec file
            
        Returns:
            Path to saved file
        """
        content = self.generate(ai_spec)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Saved .spec file to {output_path}")
        return str(output_path)


class SpecConverter:
    """Converter between .spec format and AI spec."""
    
    def __init__(self, strict: bool = True):
        """
        Initialize spec converter.
        
        Args:
            strict: Whether to use strict parsing
        """
        self.parser = SpecParser(strict=strict)
        self.generator = SpecGenerator(strict=strict)
    
    def spec_to_ai(self, spec_content: str) -> AISpec:
        """
        Convert .spec content to AI specification.
        
        Args:
            spec_content: .spec file content
            
        Returns:
            AI specification
        """
        tokens = self.parser.parse(spec_content)
        
        if self.strict:
            self.parser.validate()
        
        # Parse tokens into AI spec structure
        ai_spec_data = self._tokens_to_dict(tokens)
        return AISpec(**ai_spec_data)
    
    def _tokens_to_dict(self, tokens: List[SpecToken]) -> Dict[str, Any]:
        """
        Convert tokens to dictionary structure.
        
        Args:
            tokens: Parsed tokens
            
        Returns:
            Dictionary representation
        """
        result = {}
        current_section = None
        current_module = None
        current_requirement = None
        
        for token in tokens:
            if token.type == SpecTokenType.SECTION:
                current_section = token.key
                if current_section == "MODULES":
                    result["modules"] = []
                elif current_section == "CRITICAL_PATH":
                    result["critical_path"] = []
                elif current_section == "TOKEN_ESTIMATE":
                    result["token_estimate"] = {}
            
            elif token.type == SpecTokenType.KEY_VALUE and current_section == "METADATA":
                result[token.key] = self._parse_value(token.value)
            
            elif token.type == SpecTokenType.LIST_ITEM and current_section == "MODULES":
                # Parse module/requirement/test case hierarchy
                if token.value.startswith("module:"):
                    current_module = {"module_name": token.value.split(":")[1].strip(), "requirements": []}
                    result["modules"].append(current_module)
                elif token.value.startswith("requirement:") and current_module:
                    current_requirement = {"req_id": token.value.split(":")[1].strip(), "test_cases": []}
                    current_module["requirements"].append(current_requirement)
        
        return result
    
    def _parse_value(self, value: str) -> Any:
        """
        Parse value with type hint.
        
        Args:
            value: Value string with type hint
            
        Returns:
            Parsed value
        """
        # Extract type hint if present
        match = re.match(r'^(.+)\s+<([a-z]+)>$', value)
        if match:
            value_str, type_hint = match.groups()
            
            if type_hint == "int":
                return int(value_str)
            elif type_hint == "float":
                return float(value_str)
            elif type_hint == "bool":
                return value_str.lower() == "true"
            else:
                return value_str
        
        return value


def calculate_spec_token_count(spec_content: str) -> Dict[str, int]:
    """
    Calculate token count for .spec content.
    
    Args:
        spec_content: .spec file content
        
    Returns:
        Token count statistics
    """
    char_count = len(spec_content)
    line_count = len(spec_content.split('\n'))
    
    # Rough token estimate: 1 token ≈ 4 characters
    estimated_tokens = char_count // 4
    
    return {
        "total_characters": char_count,
        "total_lines": line_count,
        "estimated_tokens": estimated_tokens
    }
