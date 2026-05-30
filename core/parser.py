import pdfplumber
import json
import re
import logging
from typing import List, Dict, Optional, Pattern
from pathlib import Path
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass, field
from .ai_spec import AISpec, SpecConverter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FunctionalRequirement(BaseModel):
    """Represents a single functional requirement from an SRS document."""
    req_id: str = Field(..., description="Unique requirement identifier")
    title: str = Field(..., description="Requirement title")
    description: str = Field(default="", description="Detailed requirement description")
    priority: Optional[str] = Field(default=None, description="Requirement priority if specified")
    
    @validator('req_id')
    def validate_req_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Requirement ID cannot be empty")
        return v.strip()


class SRSModule(BaseModel):
    """Represents a module containing multiple functional requirements."""
    module_name: str = Field(..., description="Name of the module")
    requirements: List[FunctionalRequirement] = Field(default_factory=list)
    
    @validator('module_name')
    def validate_module_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Module name cannot be empty")
        return v.strip()


class StructuralSRS(BaseModel):
    """Complete structured SRS document with project info and modules."""
    project_name: str = Field(default="jom-QA Automated Project", description="Project name")
    modules: List[SRSModule] = Field(default_factory=list)
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")


@dataclass
class ParserConfig:
    """Configuration for SRS parser patterns and behavior."""
    module_patterns: List[str] = field(default_factory=lambda: [
        r'(?i)(?:Module|Section)\s*\d*:\s*(.*)',
        r'(?i)^\s*\d+\.\s+([^.]+)',  # Numbered sections
        r'(?i)^#{1,3}\s+(.+)'  # Markdown-style headers
    ])
    requirement_patterns: List[str] = field(default_factory=lambda: [
        r'(FR-\d+)\s*:\s*(.*)',  # FR-001: Title
        r'(REQ-\d+)\s*:\s*(.*)',  # REQ-001: Title
        r'(\d+\.\d+)\s+(.*)',  # 1.1 Title
        r'([A-Z]+-\d+)\s*:\s*(.*)'  # Generic ID-123: Title
    ])
    priority_patterns: List[str] = field(default_factory=lambda: [
        r'(?i)priority\s*:\s*(\w+)',
        r'(?i)\[(high|medium|low)\]'
    ])
    cleanup_patterns: List[tuple] = field(default_factory=lambda: [
        (r'(?i)page\s+\d+\s+of\s+\d+', ''),
        (r'\s{2,}', ' '),  # Multiple spaces to single
        (r'\n{3,}', '\n\n'),  # Multiple newlines to double
    ])
    encoding: str = 'utf-8'
    extract_tables: bool = False
    
    def compile_patterns(self) -> Dict[str, List[Pattern]]:
        """Compile all regex patterns for efficiency."""
        return {
            'module': [re.compile(p) for p in self.module_patterns],
            'requirement': [re.compile(p) for p in self.requirement_patterns],
            'priority': [re.compile(p) for p in self.priority_patterns],
            'cleanup': [(re.compile(p), r) for p, r in self.cleanup_patterns]
        }


class LocalSRSParser:
    """Enhanced SRS PDF parser with configurable patterns and robust error handling."""
    
    def __init__(self, pdf_path: str, config: Optional[ParserConfig] = None):
        """
        Initialize the SRS parser.
        
        Args:
            pdf_path: Path to the PDF file to parse
            config: Optional parser configuration. Uses default if not provided.
        """
        self.pdf_path = Path(pdf_path)
        self.config = config or ParserConfig()
        self.compiled_patterns = self.config.compile_patterns()
        
        # Validate PDF path exists
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not self.pdf_path.suffix.lower() == '.pdf':
            raise ValueError(f"File must be a PDF: {pdf_path}")
        
        logger.info(f"Initialized parser for: {self.pdf_path}")

    def extract_clean_text(self) -> str:
        """
        Extract and clean text from PDF.
        
        Returns:
            Cleaned text content from all pages
            
        Raises:
            Exception: If PDF extraction fails
        """
        try:
            clean_text = []
            total_pages = 0
            
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"Processing PDF with {total_pages} pages")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        text = page.extract_text()
                        if text:
                            # Apply cleanup patterns
                            for pattern, replacement in self.compiled_patterns['cleanup']:
                                text = pattern.sub(replacement, text)
                            clean_text.append(text)
                            
                        # Extract tables if configured
                        if self.config.extract_tables:
                            tables = page.extract_tables()
                            if tables:
                                logger.debug(f"Found {len(tables)} table(s) on page {page_num}")
                                
                    except Exception as e:
                        logger.warning(f"Error processing page {page_num}: {e}")
                        continue
            
            result = "\n".join(clean_text)
            logger.info(f"Extracted {len(result)} characters from {total_pages} pages")
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise

    def _match_requirement(self, line: str) -> Optional[tuple]:
        """Try to match line against any requirement pattern."""
        for pattern in self.compiled_patterns['requirement']:
            match = pattern.match(line)
            if match:
                return match.group(1).strip(), match.group(2).strip()
        return None

    def _match_module(self, line: str) -> Optional[str]:
        """Try to match line against any module pattern."""
        for pattern in self.compiled_patterns['module']:
            match = pattern.match(line)
            if match:
                return match.group(1).strip()
        return None

    def _extract_priority(self, text: str) -> Optional[str]:
        """Extract priority from text if present."""
        for pattern in self.compiled_patterns['priority']:
            match = pattern.search(text)
            if match:
                return match.group(1).lower()
        return None

    def filter_and_structure(self, raw_text: str) -> Dict:
        """
        Parse raw text into structured SRS format.
        
        Args:
            raw_text: Raw text extracted from PDF
            
        Returns:
            Structured SRS data as dictionary
        """
        if not raw_text or not raw_text.strip():
            logger.warning("Empty text provided for parsing")
            return StructuralSRS().model_dump()
        
        lines = raw_text.split('\n')
        srs_data = {
            "project_name": "jom-QA Automated Project",
            "modules": [],
            "metadata": {
                "total_lines": len(lines),
                "parser_version": "2.0"
            }
        }
        
        current_module = None
        stats = {
            "modules_found": 0,
            "requirements_found": 0,
            "lines_processed": 0
        }
        
        logger.info(f"Starting to parse {len(lines)} lines")
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            stats["lines_processed"] += 1
            
            if not line:
                continue
            
            # Try to match module header
            module_name = self._match_module(line)
            if module_name:
                current_module = {
                    "module_name": module_name,
                    "requirements": []
                }
                srs_data["modules"].append(current_module)
                stats["modules_found"] += 1
                logger.debug(f"Found module '{module_name}' at line {line_num}")
                continue
            
            # Try to match requirement
            req_match = self._match_requirement(line)
            if req_match and current_module is not None:
                req_id, title = req_match
                priority = self._extract_priority(line)
                
                requirement = {
                    "req_id": req_id,
                    "title": title,
                    "description": "",
                    "priority": priority
                }
                current_module["requirements"].append(requirement)
                stats["requirements_found"] += 1
                logger.debug(f"Found requirement '{req_id}: {title}' at line {line_num}")
                continue
            
            # Append description to last requirement
            if current_module and current_module["requirements"]:
                last_req = current_module["requirements"][-1]
                # Skip if line looks like a new module or requirement
                if not (self._match_module(line) or self._match_requirement(line)):
                    if line:
                        last_req["description"] += " " + line
        
        # Clean up descriptions
        for mod in srs_data["modules"]:
            for req in mod["requirements"]:
                req["description"] = req["description"].strip()
        
        srs_data["metadata"].update(stats)
        logger.info(f"Parsing complete: {stats['modules_found']} modules, {stats['requirements_found']} requirements")
        
        try:
            return StructuralSRS(**srs_data).model_dump()
        except Exception as e:
            logger.error(f"Validation error in structured data: {e}")
            # Return data without validation if it fails
            return srs_data

    def parse(self) -> Dict:
        """
        Complete parsing pipeline: extract text and structure it.
        
        Returns:
            Structured SRS data as dictionary
        """
        logger.info("Starting complete parsing pipeline")
        raw_text = self.extract_clean_text()
        structured_data = self.filter_and_structure(raw_text)
        logger.info("Parsing pipeline completed successfully")
        return structured_data

    def save_to_json(self, output_path: str, structured_data: Optional[Dict] = None) -> str:
        """
        Save structured data to JSON file.
        
        Args:
            output_path: Path to save JSON file
            structured_data: Optional pre-parsed data. Parses if not provided.
            
        Returns:
            Path to saved file
        """
        if structured_data is None:
            structured_data = self.parse()
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved structured data to {output_path}")
        return str(output_path)
    
    def to_ai_spec(self, optimize_tokens: bool = True, target_tokens: int = 4000) -> AISpec:
        """
        Convert parsed SRS to AI-optimized specification format.
        
        Args:
            optimize_tokens: Whether to optimize for minimal token consumption
            target_tokens: Target token limit for optimization
            
        Returns:
            AI-optimized specification
        """
        logger.info("Converting to AI-optimized specification format")
        
        # Parse basic SRS first
        basic_srs = self.parse()
        
        # Convert to AI spec
        ai_spec = SpecConverter.from_basic_srs(basic_srs)
        
        # Optimize for tokens if requested
        if optimize_tokens:
            ai_spec = SpecConverter.optimize_for_tokens(ai_spec, target_tokens)
            logger.info(f"Optimized spec for {target_tokens} tokens")
        
        # Log token estimates
        token_estimate = ai_spec.get_token_estimate()
        logger.info(f"Token estimate: {token_estimate['estimated_tokens']} tokens")
        
        return ai_spec
    
    def save_ai_spec(self, output_path: str, optimize_tokens: bool = True, target_tokens: int = 4000) -> str:
        """
        Parse and save AI-optimized specification to JSON file.
        
        Args:
            output_path: Path to save AI spec JSON file
            optimize_tokens: Whether to optimize for minimal token consumption
            target_tokens: Target token limit for optimization
            
        Returns:
            Path to saved file
        """
        ai_spec = self.to_ai_spec(optimize_tokens=optimize_tokens, target_tokens=target_tokens)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(ai_spec.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved AI-optimized spec to {output_path}")
        return str(output_path)
