"""FastAPI server for jom-qa engine."""
import logging
from pathlib import Path
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import shutil
import uuid

from core import LocalSRSParser, ParserConfig, AISpec, QAWorkflow, BrowserType, SpecGenerator
from config import get_config, AppConfig

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="jom-qa Engine API",
    description="AI-powered QA automation engine for parsing SRS documents",
    version="2.0.0"
)

# Load configuration
config: AppConfig = get_config()
config.setup_logging()

# Storage for parsed results
parsed_results: Dict[str, Dict] = {}


class ParseRequest(BaseModel):
    """Request model for parsing SRS document."""
    pdf_path: str
    extract_tables: bool = False
    custom_patterns: Optional[Dict[str, list]] = None


class AISpecRequest(BaseModel):
    """Request model for AI-optimized spec generation."""
    pdf_path: str
    optimize_tokens: bool = True
    target_tokens: int = 4000
    format: str = "spec"  # "spec" or "json"


class ParseResponse(BaseModel):
    """Response model for parsed SRS data."""
    job_id: str
    status: str
    project_name: str
    modules_count: int
    requirements_count: str
    data: Optional[Dict] = None


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "jom-qa Engine API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "SRS PDF parsing",
            "AI-optimized specification generation",
            ".spec format support (64.8% token reduction)",
            "Token optimization",
            "Playwright automation",
            "Professional QA workflows"
        ],
        "supported_formats": {
            "spec": "jom-qa .spec format (recommended for AI consumption)",
            "json": "Standard JSON format (for debugging)"
        },
        "endpoints": {
            "parse": "/parse",
            "upload": "/upload",
            "ai_spec": "/ai-spec",
            "ai_spec_upload": "/ai-spec/upload",
            "token_estimate": "/ai-spec/token-estimate/{job_id}",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "jom-qa-engine"
    }


@app.post("/parse", response_model=ParseResponse)
async def parse_srs(request: ParseRequest, background_tasks: BackgroundTasks):
    """
    Parse SRS PDF document and return structured data.
    
    Args:
        request: ParseRequest with PDF path and options
    
    Returns:
        ParseResponse with job ID and parsed data
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Validate PDF path exists
        pdf_path = Path(request.pdf_path)
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail=f"PDF file not found: {request.pdf_path}")
        
        # Create parser config
        parser_config = ParserConfig(extract_tables=request.extract_tables)
        
        # Apply custom patterns if provided
        if request.custom_patterns:
            if 'module_patterns' in request.custom_patterns:
                parser_config.module_patterns = request.custom_patterns['module_patterns']
            if 'requirement_patterns' in request.custom_patterns:
                parser_config.requirement_patterns = request.custom_patterns['requirement_patterns']
        
        # Parse the PDF
        parser = LocalSRSParser(str(pdf_path), config=parser_config)
        parsed_data = parser.parse()
        
        # Store result
        parsed_results[job_id] = parsed_data
        
        return ParseResponse(
            job_id=job_id,
            status="completed",
            project_name=parsed_data.get("project_name", "Unknown"),
            modules_count=len(parsed_data.get("modules", [])),
            requirements_count=sum(len(m.get("requirements", [])) for m in parsed_data.get("modules", [])),
            data=parsed_data
        )
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Parsing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")


@app.post("/upload", response_model=ParseResponse)
async def upload_and_parse(
    file: UploadFile = File(...),
    extract_tables: bool = False,
    background_tasks: BackgroundTasks = None
):
    """
    Upload and parse SRS PDF document.
    
    Args:
        file: Uploaded PDF file
        extract_tables: Whether to extract tables from PDF
    
    Returns:
        ParseResponse with job ID and parsed data
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Create uploads directory
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / f"{job_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded: {file_path}")
        
        # Parse the uploaded PDF
        parser_config = ParserConfig(extract_tables=extract_tables)
        parser = LocalSRSParser(str(file_path), config=parser_config)
        parsed_data = parser.parse()
        
        # Store result
        parsed_results[job_id] = parsed_data
        
        # Clean up uploaded file in background
        def cleanup_file():
            try:
                file_path.unlink()
                logger.info(f"Cleaned up uploaded file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup file: {e}")
        
        if background_tasks:
            background_tasks.add_task(cleanup_file)
        
        return ParseResponse(
            job_id=job_id,
            status="completed",
            project_name=parsed_data.get("project_name", "Unknown"),
            modules_count=len(parsed_data.get("modules", [])),
            requirements_count=sum(len(m.get("requirements", [])) for m in parsed_data.get("modules", [])),
            data=parsed_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload and parse error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.get("/result/{job_id}")
async def get_result(job_id: str):
    """
    Retrieve parsed result by job ID.
    
    Args:
        job_id: Job ID from previous parse request
    
    Returns:
        Parsed SRS data
    """
    if job_id not in parsed_results:
        raise HTTPException(status_code=404, detail="Job ID not found")
    
    return JSONResponse(content=parsed_results[job_id])


@app.delete("/result/{job_id}")
async def delete_result(job_id: str):
    """
    Delete parsed result by job ID.
    
    Args:
        job_id: Job ID to delete
    
    Returns:
        Confirmation message
    """
    if job_id not in parsed_results:
        raise HTTPException(status_code=404, detail="Job ID not found")
    
    del parsed_results[job_id]
    return {"message": f"Result {job_id} deleted successfully"}


@app.post("/ai-spec", response_model=ParseResponse)
async def generate_ai_spec(request: AISpecRequest):
    """
    Generate AI-optimized specification from SRS PDF.
    
    Args:
        request: AISpecRequest with PDF path and optimization settings
    
    Returns:
        ParseResponse with AI-optimized spec data
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Validate PDF path exists
        pdf_path = Path(request.pdf_path)
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail=f"PDF file not found: {request.pdf_path}")
        
        # Parse and convert to AI spec
        parser = LocalSRSParser(str(pdf_path))
        ai_spec = parser.to_ai_spec(
            optimize_tokens=request.optimize_tokens,
            target_tokens=request.target_tokens
        )
        
        # Generate output based on format
        if request.format == "spec":
            # Generate .spec format
            spec_generator = SpecGenerator(strict=True)
            spec_content = spec_generator.generate(ai_spec)
            
            # Calculate token estimate for .spec
            from core.spec_format import calculate_spec_token_count
            spec_stats = calculate_spec_token_count(spec_content)
            
            result_data = {
                "format": "spec",
                "content": spec_content,
                "token_estimate": spec_stats,
                "ai_spec": ai_spec.model_dump()
            }
        else:
            # Default to JSON format
            result_data = ai_spec.model_dump()
        
        # Store result
        parsed_results[job_id] = result_data
        
        return ParseResponse(
            job_id=job_id,
            status="completed",
            project_name=ai_spec.project_name,
            modules_count=len(ai_spec.modules),
            requirements_count=ai_spec.total_requirements,
            data=result_data
        )
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"AI spec generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI spec: {str(e)}")


@app.post("/ai-spec/upload")
async def upload_and_generate_ai_spec(
    file: UploadFile = File(...),
    optimize_tokens: bool = True,
    target_tokens: int = 4000,
    format: str = "spec"
):
    """
    Upload PDF and generate AI-optimized specification.
    
    Args:
        file: Uploaded PDF file
        optimize_tokens: Whether to optimize for minimal token consumption
        target_tokens: Target token limit
        format: Output format ("spec" or "json")
    
    Returns:
        AI-optimized specification
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Create uploads directory
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / f"{job_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded: {file_path}")
        
        # Parse and convert to AI spec
        parser = LocalSRSParser(str(file_path))
        ai_spec = parser.to_ai_spec(
            optimize_tokens=optimize_tokens,
            target_tokens=target_tokens
        )
        
        # Generate output based on format
        if format == "spec":
            spec_generator = SpecGenerator(strict=True)
            spec_content = spec_generator.generate(ai_spec)
            
            from core.spec_format import calculate_spec_token_count
            spec_stats = calculate_spec_token_count(spec_content)
            
            result_data = {
                "format": "spec",
                "content": spec_content,
                "token_estimate": spec_stats,
                "ai_spec": ai_spec.model_dump()
            }
        else:
            result_data = ai_spec.model_dump()
        
        # Store result
        parsed_results[job_id] = result_data
        
        # Clean up uploaded file
        file_path.unlink()
        logger.info(f"Cleaned up uploaded file: {file_path}")
        
        return JSONResponse(content={
            "job_id": job_id,
            "status": "completed",
            "project_name": ai_spec.project_name,
            "modules_count": len(ai_spec.modules),
            "requirements_count": ai_spec.total_requirements,
            "test_cases_count": ai_spec.total_test_cases,
            "format": format,
            "token_estimate": result_data.get("token_estimate") if format == "spec" else ai_spec.get_token_estimate(),
            "data": result_data
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload and AI spec generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.get("/ai-spec/token-estimate/{job_id}")
async def get_token_estimate(job_id: str):
    """
    Get token estimate for AI spec.
    
    Args:
        job_id: Job ID from previous AI spec generation
    
    Returns:
        Token consumption estimate
    """
    if job_id not in parsed_results:
        raise HTTPException(status_code=404, detail="Job ID not found")
    
    spec_data = parsed_results[job_id]
    
    # Calculate token estimate
    char_count = len(str(spec_data))
    estimated_tokens = char_count // 4
    
    return {
        "job_id": job_id,
        "total_characters": char_count,
        "estimated_tokens": estimated_tokens,
        "modules": len(spec_data.get("modules", [])),
        "requirements": spec_data.get("total_requirements", 0),
        "test_cases": spec_data.get("total_test_cases", 0)
    }


def start_server():
    """Start the FastAPI server."""
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.api_debug
    )


if __name__ == "__main__":
    start_server()
