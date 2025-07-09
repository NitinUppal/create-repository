import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contract_scanner import ContractData

# Configure logging
logger = logging.getLogger(__name__)

Base = declarative_base()

class ContractRecord(Base):
    """SQLAlchemy model for contract data"""
    __tablename__ = 'contracts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    contract_type = Column(String(100))
    parties = Column(JSON)  # Store as JSON array
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    value = Column(Float)
    currency = Column(String(10))
    key_terms = Column(JSON)  # Store as JSON array
    clauses = Column(JSON)  # Store as JSON object
    extracted_text = Column(Text)
    extraction_date = Column(DateTime, default=datetime.now)
    confidence_score = Column(Float)

class DatabaseManager:
    """Database manager for storing contract data"""
    
    def __init__(self, database_url: str = "sqlite:///contracts.db"):
        """
        Initialize database manager
        
        Args:
            database_url: Database connection string
                Examples:
                - SQLite: "sqlite:///contracts.db"
                - PostgreSQL: "postgresql://user:password@localhost/contracts"
                - MySQL: "mysql+pymysql://user:password@localhost/contracts"
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Database initialized with URL: {database_url}")
    
    def get_db(self) -> Session:
        """Get database session"""
        db = self.SessionLocal()
        try:
            return db
        except Exception:
            db.close()
            raise
    
    def store_contract(self, contract_data: ContractData) -> int:
        """Store a single contract in the database"""
        db = self.get_db()
        try:
            # Convert ContractData to database record
            db_contract = ContractRecord(
                file_path=contract_data.file_path,
                file_name=contract_data.file_name,
                contract_type=contract_data.contract_type,
                parties=contract_data.parties,
                start_date=contract_data.start_date,
                end_date=contract_data.end_date,
                value=contract_data.value,
                currency=contract_data.currency,
                key_terms=contract_data.key_terms,
                clauses=contract_data.clauses,
                extracted_text=contract_data.extracted_text,
                extraction_date=contract_data.extraction_date,
                confidence_score=contract_data.confidence_score
            )
            
            db.add(db_contract)
            db.commit()
            db.refresh(db_contract)
            
            logger.info(f"Stored contract: {contract_data.file_name} with ID: {db_contract.id}")
            return db_contract.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing contract {contract_data.file_name}: {str(e)}")
            raise
        finally:
            db.close()
    
    def store_contracts(self, contracts: List[ContractData]) -> List[int]:
        """Store multiple contracts in the database"""
        stored_ids = []
        for contract in contracts:
            try:
                contract_id = self.store_contract(contract)
                stored_ids.append(contract_id)
            except Exception as e:
                logger.error(f"Failed to store contract {contract.file_name}: {str(e)}")
        
        logger.info(f"Stored {len(stored_ids)} out of {len(contracts)} contracts")
        return stored_ids
    
    def get_contract_by_id(self, contract_id: int) -> Optional[ContractRecord]:
        """Retrieve a contract by ID"""
        db = self.get_db()
        try:
            contract = db.query(ContractRecord).filter(ContractRecord.id == contract_id).first()
            return contract
        finally:
            db.close()
    
    def get_contracts_by_type(self, contract_type: str) -> List[ContractRecord]:
        """Retrieve contracts by type"""
        db = self.get_db()
        try:
            contracts = db.query(ContractRecord).filter(
                ContractRecord.contract_type == contract_type
            ).all()
            return contracts
        finally:
            db.close()
    
    def get_contracts_by_party(self, party_name: str) -> List[ContractRecord]:
        """Retrieve contracts involving a specific party"""
        db = self.get_db()
        try:
            # Search for party name in JSON array
            contracts = db.query(ContractRecord).filter(
                ContractRecord.parties.contains([party_name])
            ).all()
            return contracts
        finally:
            db.close()
    
    def get_contracts_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ContractRecord]:
        """Retrieve contracts within a date range"""
        db = self.get_db()
        try:
            contracts = db.query(ContractRecord).filter(
                ContractRecord.start_date >= start_date,
                ContractRecord.end_date <= end_date
            ).all()
            return contracts
        finally:
            db.close()
    
    def get_contracts_by_value_range(self, min_value: float, max_value: float) -> List[ContractRecord]:
        """Retrieve contracts within a value range"""
        db = self.get_db()
        try:
            contracts = db.query(ContractRecord).filter(
                ContractRecord.value >= min_value,
                ContractRecord.value <= max_value
            ).all()
            return contracts
        finally:
            db.close()
    
    def search_contracts(self, search_term: str) -> List[ContractRecord]:
        """Search contracts by text content"""
        db = self.get_db()
        try:
            contracts = db.query(ContractRecord).filter(
                ContractRecord.extracted_text.contains(search_term)
            ).all()
            return contracts
        finally:
            db.close()
    
    def get_all_contracts(self, limit: Optional[int] = None) -> List[ContractRecord]:
        """Retrieve all contracts with optional limit"""
        db = self.get_db()
        try:
            query = db.query(ContractRecord)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            db.close()
    
    def update_contract(self, contract_id: int, **kwargs) -> bool:
        """Update contract fields"""
        db = self.get_db()
        try:
            contract = db.query(ContractRecord).filter(ContractRecord.id == contract_id).first()
            if not contract:
                return False
            
            for key, value in kwargs.items():
                if hasattr(contract, key):
                    setattr(contract, key, value)
            
            db.commit()
            logger.info(f"Updated contract ID: {contract_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating contract {contract_id}: {str(e)}")
            return False
        finally:
            db.close()
    
    def delete_contract(self, contract_id: int) -> bool:
        """Delete a contract by ID"""
        db = self.get_db()
        try:
            contract = db.query(ContractRecord).filter(ContractRecord.id == contract_id).first()
            if not contract:
                return False
            
            db.delete(contract)
            db.commit()
            logger.info(f"Deleted contract ID: {contract_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting contract {contract_id}: {str(e)}")
            return False
        finally:
            db.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        db = self.get_db()
        try:
            total_contracts = db.query(ContractRecord).count()
            
            # Count by contract type
            contract_types = db.query(ContractRecord.contract_type).distinct().all()
            type_counts = {}
            for contract_type in contract_types:
                if contract_type[0]:
                    count = db.query(ContractRecord).filter(
                        ContractRecord.contract_type == contract_type[0]
                    ).count()
                    type_counts[contract_type[0]] = count
            
            # Average contract value
            avg_value = db.query(ContractRecord.value).filter(
                ContractRecord.value.isnot(None)
            ).all()
            avg_value = sum([v[0] for v in avg_value]) / len(avg_value) if avg_value else 0
            
            return {
                "total_contracts": total_contracts,
                "contract_types": type_counts,
                "average_value": avg_value,
                "database_url": self.database_url
            }
        finally:
            db.close()
    
    def export_to_json(self, filename: str = "contracts_export.json") -> bool:
        """Export all contracts to JSON file"""
        try:
            contracts = self.get_all_contracts()
            
            export_data = []
            for contract in contracts:
                contract_dict = {
                    "id": contract.id,
                    "file_path": contract.file_path,
                    "file_name": contract.file_name,
                    "contract_type": contract.contract_type,
                    "parties": contract.parties,
                    "start_date": contract.start_date.isoformat() if contract.start_date else None,
                    "end_date": contract.end_date.isoformat() if contract.end_date else None,
                    "value": contract.value,
                    "currency": contract.currency,
                    "key_terms": contract.key_terms,
                    "clauses": contract.clauses,
                    "extracted_text": contract.extracted_text,
                    "extraction_date": contract.extraction_date.isoformat() if contract.extraction_date else None,
                    "confidence_score": contract.confidence_score
                }
                export_data.append(contract_dict)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(export_data)} contracts to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")
            return False