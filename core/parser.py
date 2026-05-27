import pdfplumber
import json
import re
from typing import List, Dict
from pydantic import BaseModel

class FunctionalRequirement(BaseModel):
    req_id: str
    title: str
    description: str

class SRSModule(BaseModel):
    module_name: str
    requirements: List[FunctionalRequirement]

class StructuralSRS(BaseModel):
    project_name: str
    modules: List[SRSModule]

class LocalSRSParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def extract_clean_text(self) -> str:
        clean_text = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text = re.sub(r'(?i)page\s+\d+\s+of\s+\d+', '', text)
                    clean_text.append(text)
        return "\n".join(clean_text)

    def filter_and_structure(self, raw_text: str) -> Dict:
        lines = raw_text.split('\n')
        srs_data = {"project_name": "jom-QA Automated Project", "modules": []}
        current_module = None
        
        # Sesuai untuk pattern standard: "Module: Authentication" & "FR-001: User Login"
        module_pattern = re.compile(r'(?i)(?:Module|Section)\s*\d*:\s*(.*)')
        fr_pattern = re.compile(r'(FR-\d+)\s*:\s*(.*)')

        for line in lines:
            line = line.strip()
            module_match = module_pattern.match(line)
            if module_match:
                current_module = {"module_name": module_match.group(1).strip(), "requirements": []}
                srs_data["modules"].append(current_module)
                continue
            
            fr_match = fr_pattern.match(line)
            if fr_match and current_module is not None:
                requirement = {"req_id": fr_match.group(1).strip(), "title": fr_match.group(2).strip(), "description": ""}
                current_module["requirements"].append(requirement)
                continue
                
            if current_module and current_module["requirements"]:
                last_req = current_module["requirements"][-1]
                if line and not line.startswith(('Module', 'FR-')):
                    last_req["description"] += " " + line

        for mod in srs_data["modules"]:
            for req in mod["requirements"]:
                req["description"] = req["description"].strip()

        return StructuralSRS(**srs_data).model_dump()
