THIS SHOULD BE A LINTER ERRORimport os
import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document
import spacy
import dateparser
from pydantic import BaseModel
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContractData(BaseModel):
    """Pydantic model for contract data structure"""
    file_path: str
    file_name: str
    contract_type: Optional[str] = None
    parties: List[str] = []
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    value: Optional[float] = None
    currency: Optional[str] = None
    key_terms: List[str] = []
    clauses: Dict[str, str] = {}
    extracted_text: str = ""
    extraction_date: datetime = datetime.now()
    confidence_score: Optional[float] = None

class ContractScanner:
    """Main class for scanning and extracting data from contracts"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the contract scanner"""
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Load spaCy model for NLP processing
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {str(e)}")
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error extracting text from TXT {file_path}: {str(e)}")
            return ""
    
    def extract_text(self, file_path: str) -> str:
        """Extract text based on file extension"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_ext == '.docx':
            return self.extract_text_from_docx(file_path)
        elif file_ext == '.txt':
            return self.extract_text_from_txt(file_path)
        else:
            logger.warning(f"Unsupported file format: {file_ext}")
            return ""
    
    def extract_parties_with_nlp(self, text: str) -> List[str]:
        """Extract parties using NLP"""
        if not self.nlp:
            return self.extract_parties_with_regex(text)
        
        doc = self.nlp(text)
        parties = set()
        
        # Extract organizations and persons
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PERSON"]:
                parties.add(ent.text.strip())
        
        return list(parties)
    
    def extract_parties_with_regex(self, text: str) -> List[str]:
        """Extract parties using regex patterns"""
        patterns = [
            r'between\s+([^,]+),?\s+and\s+([^,\n]+)',
            r'parties?:\s*([^,\n]+)(?:,\s*and\s+([^,\n]+))?',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+(?:Inc|LLC|Corp|Company|Ltd))?\s*)',
        ]
        
        parties = set()
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                for group in match.groups():
                    if group:
                        parties.add(group.strip())
        
        return list(parties)
    
    def extract_dates(self, text: str) -> Dict[str, Optional[datetime]]:
        """Extract start and end dates from contract text"""
        date_patterns = [
            r'effective\s+date[:\s]*([^,\n]+)',
            r'commencement\s+date[:\s]*([^,\n]+)',
            r'start\s+date[:\s]*([^,\n]+)',
            r'termination\s+date[:\s]*([^,\n]+)',
            r'end\s+date[:\s]*([^,\n]+)',
            r'expires?\s+on[:\s]*([^,\n]+)',
            r'from\s+([^,\n]+)\s+to\s+([^,\n]+)',
        ]
        
        dates = {"start_date": None, "end_date": None}
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                for i, group in enumerate(match.groups()):
                    if group:
                        parsed_date = dateparser.parse(group.strip())
                        if parsed_date:
                            if 'start' in pattern or 'effective' in pattern or 'commencement' in pattern:
                                dates["start_date"] = parsed_date
                            elif 'end' in pattern or 'termination' in pattern or 'expires' in pattern:
                                dates["end_date"] = parsed_date
                            elif i == 0:  # First date in range
                                dates["start_date"] = parsed_date
                            elif i == 1:  # Second date in range
                                dates["end_date"] = parsed_date
        
        return dates
    
    def extract_financial_info(self, text: str) -> Dict[str, Optional[Union[float, str]]]:
        """Extract financial information from contract"""
        # Currency patterns
        currency_pattern = r'\b(USD|EUR|GBP|CAD|AUD|JPY|\$|€|£)\b'
        
        # Amount patterns
        amount_patterns = [
            r'(?:amount|value|price|cost|fee|payment)[:\s]*\$?([\d,]+\.?\d*)',
            r'\$?([\d,]+\.?\d*)\s*(?:dollars?|USD)',
            r'total[:\s]*\$?([\d,]+\.?\d*)',
        ]
        
        currency_matches = re.findall(currency_pattern, text, re.IGNORECASE)
        currency = currency_matches[0] if currency_matches else None
        
        value = None
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    # Remove commas and convert to float
                    value = float(matches[0].replace(',', ''))
                    break
                except ValueError:
                    continue
        
        return {"value": value, "currency": currency}
    
    def extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms and clauses"""
        key_terms = []
        
        # Common contract terms to look for
        term_patterns = [
            r'confidentiality[^.]*\.',
            r'non-disclosure[^.]*\.',
            r'intellectual property[^.]*\.',
            r'termination[^.]*\.',
            r'liability[^.]*\.',
            r'indemnification[^.]*\.',
            r'governing law[^.]*\.',
            r'dispute resolution[^.]*\.',
        ]
        
        for pattern in term_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            key_terms.extend([match.strip() for match in matches])
        
        return key_terms
    
    def analyze_with_ai(self, text: str) -> Dict:
        """Use OpenAI to analyze contract (if API key available)"""
        if not self.openai_api_key:
            return {}
        
        try:
            prompt = f"""
            Analyze the following contract text and extract structured information:
            
            {text[:3000]}  # Limit text to avoid token limits
            
            Please extract and return in JSON format:
            1. Contract type (e.g., "Service Agreement", "NDA", "Employment Contract")
            2. Parties involved
            3. Key dates (start, end)
            4. Financial terms (amount, currency)
            5. Important clauses
            6. Confidence score (0-1) for the extraction
            
            Return only valid JSON.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
        
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return {}
    
    def scan_contract(self, file_path: str) -> ContractData:
        """Main method to scan a contract and extract structured data"""
        logger.info(f"Scanning contract: {file_path}")
        
        # Extract text
        text = self.extract_text(file_path)
        if not text:
            logger.error(f"Could not extract text from {file_path}")
            return ContractData(file_path=file_path, file_name=Path(file_path).name)
        
        # Extract parties
        parties = self.extract_parties_with_nlp(text)
        
        # Extract dates
        dates = self.extract_dates(text)
        
        # Extract financial information
        financial_info = self.extract_financial_info(text)
        
        # Extract key terms
        key_terms = self.extract_key_terms(text)
        
        # AI analysis (if available)
        ai_analysis = self.analyze_with_ai(text)
        
        # Merge AI results with extracted data
        contract_type = ai_analysis.get('contract_type')
        confidence_score = ai_analysis.get('confidence_score')
        
        # Create structured data
        contract_data = ContractData(
            file_path=file_path,
            file_name=Path(file_path).name,
            contract_type=contract_type,
            parties=parties,
            start_date=dates.get('start_date'),
            end_date=dates.get('end_date'),
            value=financial_info.get('value'),
            currency=financial_info.get('currency'),
            key_terms=key_terms,
            extracted_text=text[:1000],  # Store first 1000 chars
            confidence_score=confidence_score
        )
        
        logger.info(f"Successfully scanned contract: {file_path}")
        return contract_data
    
    def scan_directory(self, directory_path: str) -> List[ContractData]:
        """Scan all contracts in a directory"""
        directory = Path(directory_path)
        contracts = []
        
        supported_extensions = ['.pdf', '.docx', '.txt']
        
        for file_path in directory.rglob('*'):
            if file_path.suffix.lower() in supported_extensions:
                try:
                    contract_data = self.scan_contract(str(file_path))
                    contracts.append(contract_data)
                except Exception as e:
                    logger.error(f"Error scanning {file_path}: {str(e)}")
        
        return contracts