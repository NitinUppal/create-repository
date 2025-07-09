# Contract Scanner System

A comprehensive Python application for scanning, analyzing, and storing contract data in structured format. This system can extract key information from contracts in various formats (PDF, DOCX, TXT) and store it in a database for easy retrieval and analysis.

## Features

- **Multi-format Support**: Extracts text from PDF, DOCX, and TXT files
- **Intelligent Data Extraction**: Uses NLP and regex patterns to identify:
  - Contract parties (organizations and individuals)
  - Start and end dates
  - Financial information (amounts and currencies)
  - Key contract terms and clauses
- **Database Storage**: Stores structured data in SQLite, PostgreSQL, or MySQL
- **Search and Query**: Advanced search capabilities by party, type, date range, value, etc.
- **Data Export**: Export contracts to JSON format
- **Command Line Interface**: Full CLI with interactive mode
- **OpenAI Integration**: Optional AI-powered analysis for enhanced accuracy

## Installation

1. **Clone or download the project files**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install spaCy language model** (optional but recommended for better NLP):
```bash
python -m spacy download en_core_web_sm
```

4. **Set up environment variables** (optional):
```bash
cp .env.example .env
# Edit .env file with your configuration
```

## Dependencies

- `pymupdf`: PDF text extraction
- `python-docx`: DOCX file processing
- `sqlalchemy`: Database ORM
- `pydantic`: Data validation and serialization
- `spacy`: Natural language processing
- `dateparser`: Date parsing and normalization
- `openai`: AI-powered analysis (optional)
- `python-dotenv`: Environment variable management

## Quick Start

### Basic Usage

```python
from contract_scanner import ContractScanner
from database_manager import DatabaseManager

# Initialize scanner
scanner = ContractScanner()

# Scan a single contract
contract_data = scanner.scan_contract("path/to/contract.pdf")

# Store in database
db_manager = DatabaseManager("sqlite:///contracts.db")
contract_id = db_manager.store_contract(contract_data)

print(f"Contract stored with ID: {contract_id}")
```

### Command Line Usage

```bash
# Scan a single file
python main.py --file contract.pdf

# Scan entire directory
python main.py --directory ./contracts/

# Interactive mode
python main.py --interactive

# Search contracts
python main.py --search "confidentiality"
python main.py --party "TechCorp"
python main.py --type "Service Agreement"

# View statistics
python main.py --stats

# Export data
python main.py --export contracts_backup.json
```

## System Architecture

### Core Components

1. **ContractScanner** (`contract_scanner.py`)
   - Main extraction engine
   - Handles multiple file formats
   - Implements NLP and regex-based parsing
   - Optional OpenAI integration

2. **DatabaseManager** (`database_manager.py`)
   - Database abstraction layer
   - Supports SQLite, PostgreSQL, MySQL
   - CRUD operations and advanced queries
   - Data export functionality

3. **ContractScannerApp** (`main.py`)
   - Main application interface
   - Command-line argument parsing
   - Interactive mode implementation

### Data Structure

The system extracts and stores the following contract information:

```python
class ContractData:
    file_path: str                    # Original file location
    file_name: str                    # File name
    contract_type: str                # Type of contract (if identified)
    parties: List[str]                # Involved parties
    start_date: datetime              # Contract start date
    end_date: datetime                # Contract end date
    value: float                      # Financial value
    currency: str                     # Currency (USD, EUR, etc.)
    key_terms: List[str]              # Important clauses/terms
    clauses: Dict[str, str]           # Detailed clause mapping
    extracted_text: str               # First 1000 chars of text
    extraction_date: datetime         # When the extraction was performed
    confidence_score: float           # AI confidence (if using OpenAI)
```

## Configuration

### Database Configuration

The system supports multiple database backends:

```python
# SQLite (default)
db_manager = DatabaseManager("sqlite:///contracts.db")

# PostgreSQL
db_manager = DatabaseManager("postgresql://user:password@localhost/contracts")

# MySQL
db_manager = DatabaseManager("mysql+pymysql://user:password@localhost/contracts")
```

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# OpenAI API Key (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Database URL
DATABASE_URL=sqlite:///contracts.db

# Logging level
LOG_LEVEL=INFO
```

## Advanced Usage

### Directory Scanning

```python
# Scan all contracts in a directory
scanner = ContractScanner()
contracts = scanner.scan_directory("./contracts/")

# Store all in database
db_manager = DatabaseManager()
stored_ids = db_manager.store_contracts(contracts)
```

### Advanced Queries

```python
# Search by date range
from datetime import datetime
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)
contracts = db_manager.get_contracts_by_date_range(start_date, end_date)

# Search by value range
high_value = db_manager.get_contracts_by_value_range(50000, 1000000)

# Text search
results = db_manager.search_contracts("intellectual property")

# Get statistics
stats = db_manager.get_statistics()
```

### Custom Extraction Patterns

You can extend the extraction patterns by modifying the regex patterns in `contract_scanner.py`:

```python
# Add custom party patterns
custom_patterns = [
    r'contractor:\s*([^,\n]+)',
    r'vendor:\s*([^,\n]+)',
]

# Add custom date patterns
date_patterns = [
    r'signature\s+date[:\s]*([^,\n]+)',
    r'execution\s+date[:\s]*([^,\n]+)',
]
```

## API Reference

### ContractScanner Class

```python
class ContractScanner:
    def __init__(self, openai_api_key: Optional[str] = None)
    def scan_contract(self, file_path: str) -> ContractData
    def scan_directory(self, directory_path: str) -> List[ContractData]
    def extract_text(self, file_path: str) -> str
    def extract_parties_with_nlp(self, text: str) -> List[str]
    def extract_dates(self, text: str) -> Dict[str, Optional[datetime]]
    def extract_financial_info(self, text: str) -> Dict[str, Union[float, str]]
    def extract_key_terms(self, text: str) -> List[str]
```

### DatabaseManager Class

```python
class DatabaseManager:
    def __init__(self, database_url: str = "sqlite:///contracts.db")
    def store_contract(self, contract_data: ContractData) -> int
    def store_contracts(self, contracts: List[ContractData]) -> List[int]
    def get_contract_by_id(self, contract_id: int) -> Optional[ContractRecord]
    def get_contracts_by_type(self, contract_type: str) -> List[ContractRecord]
    def get_contracts_by_party(self, party_name: str) -> List[ContractRecord]
    def get_contracts_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ContractRecord]
    def search_contracts(self, search_term: str) -> List[ContractRecord]
    def get_statistics(self) -> Dict[str, Any]
    def export_to_json(self, filename: str) -> bool
```

## Error Handling

The system includes comprehensive error handling:

- **File Access Errors**: Graceful handling of missing or corrupted files
- **Database Errors**: Transaction rollback and error logging
- **Parsing Errors**: Continues processing even if some fields can't be extracted
- **API Errors**: Fallback to local processing if OpenAI API fails

## Performance Considerations

- **Large Files**: PDF processing is memory-efficient for large documents
- **Batch Processing**: Directory scanning processes files sequentially with error isolation
- **Database Optimization**: Uses indexes on commonly queried fields
- **Memory Management**: Text extraction is limited to prevent memory issues

## Testing

Run the example script to test the system:

```bash
python example_usage.py
```

This script demonstrates:
- Single file scanning
- Database storage and retrieval
- Directory scanning
- Advanced queries
- Data export

## Troubleshooting

### Common Issues

1. **spaCy model not found**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

2. **Database connection errors**:
   - Check database URL format
   - Ensure database server is running
   - Verify credentials

3. **PDF extraction issues**:
   - Some PDFs may be image-based (require OCR)
   - Encrypted PDFs need password

4. **Memory issues with large files**:
   - Process files in smaller batches
   - Increase system memory
   - Use text length limits

### Debugging

Enable verbose logging:

```bash
python main.py --verbose --file contract.pdf
```

Check log file:
```bash
tail -f contract_scanner.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues:
1. Check the troubleshooting section
2. Review the example usage script
3. Enable verbose logging for debugging
4. Create an issue with detailed error information

## Future Enhancements

- OCR support for image-based PDFs
- Additional file format support (RTF, HTML)
- Web interface for contract management
- Machine learning for contract classification
- Integration with document management systems
- Automated contract renewal tracking