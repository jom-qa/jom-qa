"""Unit tests for SRS parser."""
import pytest
from pathlib import Path
from core import LocalSRSParser, ParserConfig, FunctionalRequirement, SRSModule, StructuralSRS


class TestParserConfig:
    """Test ParserConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ParserConfig()
        assert config.extract_tables is False
        assert config.encoding == 'utf-8'
        assert len(config.module_patterns) > 0
        assert len(config.requirement_patterns) > 0
    
    def test_compile_patterns(self):
        """Test pattern compilation."""
        config = ParserConfig()
        compiled = config.compile_patterns()
        assert 'module' in compiled
        assert 'requirement' in compiled
        assert 'priority' in compiled
        assert 'cleanup' in compiled
        assert len(compiled['module']) == len(config.module_patterns)


class TestFunctionalRequirement:
    """Test FunctionalRequirement model."""
    
    def test_valid_requirement(self):
        """Test creating valid requirement."""
        req = FunctionalRequirement(
            req_id="FR-001",
            title="User Login",
            description="User should be able to login"
        )
        assert req.req_id == "FR-001"
        assert req.title == "User Login"
        assert req.description == "User should be able to login"
    
    def test_empty_req_id_raises_error(self):
        """Test that empty req_id raises validation error."""
        with pytest.raises(ValueError):
            FunctionalRequirement(
                req_id="",
                title="Test"
            )
    
    def test_whitespace_req_id_gets_stripped(self):
        """Test that req_id whitespace is stripped."""
        req = FunctionalRequirement(
            req_id="  FR-001  ",
            title="Test"
        )
        assert req.req_id == "FR-001"


class TestSRSModule:
    """Test SRSModule model."""
    
    def test_valid_module(self):
        """Test creating valid module."""
        req = FunctionalRequirement(req_id="FR-001", title="Test")
        module = SRSModule(
            module_name="Authentication",
            requirements=[req]
        )
        assert module.module_name == "Authentication"
        assert len(module.requirements) == 1
    
    def test_empty_module_name_raises_error(self):
        """Test that empty module name raises validation error."""
        with pytest.raises(ValueError):
            SRSModule(module_name="", requirements=[])


class TestStructuralSRS:
    """Test StructuralSRS model."""
    
    def test_valid_srs(self):
        """Test creating valid SRS structure."""
        req = FunctionalRequirement(req_id="FR-001", title="Test")
        module = SRSModule(module_name="Auth", requirements=[req])
        srs = StructuralSRS(
            project_name="Test Project",
            modules=[module]
        )
        assert srs.project_name == "Test Project"
        assert len(srs.modules) == 1


class TestLocalSRSParser:
    """Test LocalSRSParser class."""
    
    def test_parser_initialization_with_invalid_path(self):
        """Test parser initialization with non-existent file."""
        with pytest.raises(FileNotFoundError):
            LocalSRSParser("nonexistent.pdf")
    
    def test_parser_initialization_with_non_pdf(self):
        """Test parser initialization with non-PDF file."""
        # Create a temporary text file
        test_file = Path("test.txt")
        test_file.write_text("test")
        
        try:
            with pytest.raises(ValueError):
                LocalSRSParser(str(test_file))
        finally:
            test_file.unlink()
    
    def test_match_requirement(self):
        """Test requirement pattern matching."""
        config = ParserConfig()
        parser = LocalSRSParser.__new__(LocalSRSParser)
        parser.config = config
        parser.compiled_patterns = config.compile_patterns()
        
        # Test FR pattern
        result = parser._match_requirement("FR-001: User Login")
        assert result is not None
        assert result[0] == "FR-001"
        assert result[1] == "User Login"
        
        # Test REQ pattern
        result = parser._match_requirement("REQ-123: Test Requirement")
        assert result is not None
        assert result[0] == "REQ-123"
    
    def test_match_module(self):
        """Test module pattern matching."""
        config = ParserConfig()
        parser = LocalSRSParser.__new__(LocalSRSParser)
        parser.config = config
        parser.compiled_patterns = config.compile_patterns()
        
        # Test Module pattern
        result = parser._match_module("Module: Authentication")
        assert result == "Authentication"
        
        # Test Section pattern
        result = parser._match_module("Section 1: User Management")
        assert result == "User Management"
    
    def test_extract_priority(self):
        """Test priority extraction."""
        config = ParserConfig()
        parser = LocalSRSParser.__new__(LocalSRSParser)
        parser.config = config
        parser.compiled_patterns = config.compile_patterns()
        
        # Test priority pattern
        result = parser._extract_priority("Priority: High")
        assert result == "high"
        
        # Test bracket pattern
        result = parser._extract_priority("[High] User Login")
        assert result == "high"
    
    def test_filter_and_structure_with_empty_text(self):
        """Test parsing with empty text."""
        config = ParserConfig()
        parser = LocalSRSParser.__new__(LocalSRSParser)
        parser.config = config
        parser.compiled_patterns = config.compile_patterns()
        
        result = parser.filter_and_structure("")
        assert result is not None
        assert "modules" in result
    
    def test_filter_and_structure_with_sample_text(self):
        """Test parsing with sample SRS text."""
        config = ParserConfig()
        parser = LocalSRSParser.__new__(LocalSRSParser)
        parser.config = config
        parser.compiled_patterns = config.compile_patterns()
        
        sample_text = """
        Module: Authentication
        FR-001: User Login
        User should be able to login with email and password
        FR-002: User Registration
        New users can register for an account
        
        Module: User Management
        FR-003: Profile Update
        Users can update their profile information
        """
        
        result = parser.filter_and_structure(sample_text)
        assert len(result["modules"]) == 2
        assert result["modules"][0]["module_name"] == "Authentication"
        assert len(result["modules"][0]["requirements"]) == 2
        assert result["modules"][0]["requirements"][0]["req_id"] == "FR-001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
