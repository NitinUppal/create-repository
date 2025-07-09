#!/usr/bin/env python3
"""
Contract Scanner Application
Main entry point for scanning contracts and storing structured data in database
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional

from contract_scanner import ContractScanner, ContractData
from database_manager import DatabaseManager, ContractRecord

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('contract_scanner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ContractScannerApp:
    """Main application class for contract scanning"""
    
    def __init__(self, database_url: str = "sqlite:///contracts.db", openai_api_key: Optional[str] = None):
        """Initialize the application"""
        self.scanner = ContractScanner(openai_api_key=openai_api_key)
        self.db_manager = DatabaseManager(database_url=database_url)
        logger.info("Contract Scanner Application initialized")
    
    def scan_single_file(self, file_path: str) -> Optional[int]:
        """Scan a single contract file and store in database"""
        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        try:
            # Scan the contract
            contract_data = self.scanner.scan_contract(file_path)
            
            # Store in database
            contract_id = self.db_manager.store_contract(contract_data)
            
            logger.info(f"Successfully processed {file_path} with ID: {contract_id}")
            return contract_id
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            return None
    
    def scan_directory(self, directory_path: str) -> List[int]:
        """Scan all contracts in a directory and store in database"""
        if not Path(directory_path).exists():
            logger.error(f"Directory not found: {directory_path}")
            return []
        
        try:
            # Scan all contracts in directory
            contracts = self.scanner.scan_directory(directory_path)
            
            # Store all contracts in database
            stored_ids = self.db_manager.store_contracts(contracts)
            
            logger.info(f"Successfully processed {len(stored_ids)} contracts from {directory_path}")
            return stored_ids
            
        except Exception as e:
            logger.error(f"Error processing directory {directory_path}: {str(e)}")
            return []
    
    def search_contracts(self, **criteria) -> List[ContractRecord]:
        """Search contracts based on various criteria"""
        results = []
        
        if 'contract_type' in criteria:
            results.extend(self.db_manager.get_contracts_by_type(criteria['contract_type']))
        
        if 'party_name' in criteria:
            results.extend(self.db_manager.get_contracts_by_party(criteria['party_name']))
        
        if 'search_term' in criteria:
            results.extend(self.db_manager.search_contracts(criteria['search_term']))
        
        if 'min_value' in criteria and 'max_value' in criteria:
            results.extend(self.db_manager.get_contracts_by_value_range(
                criteria['min_value'], criteria['max_value']
            ))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_results = []
        for contract in results:
            if contract.id not in seen:
                seen.add(contract.id)
                unique_results.append(contract)
        
        return unique_results
    
    def display_contract_summary(self, contract: ContractRecord):
        """Display a summary of a contract"""
        print(f"\n--- Contract ID: {contract.id} ---")
        print(f"File: {contract.file_name}")
        print(f"Type: {contract.contract_type or 'Unknown'}")
        print(f"Parties: {', '.join(contract.parties) if contract.parties else 'Not identified'}")
        print(f"Start Date: {contract.start_date or 'Not specified'}")
        print(f"End Date: {contract.end_date or 'Not specified'}")
        if contract.value:
            print(f"Value: {contract.currency or ''} {contract.value:,.2f}")
        print(f"Key Terms: {len(contract.key_terms) if contract.key_terms else 0} identified")
        print(f"Extraction Date: {contract.extraction_date}")
        if contract.confidence_score:
            print(f"Confidence Score: {contract.confidence_score:.2f}")
        print("-" * 50)
    
    def display_statistics(self):
        """Display database statistics"""
        stats = self.db_manager.get_statistics()
        
        print("\n=== Contract Database Statistics ===")
        print(f"Total Contracts: {stats['total_contracts']}")
        print(f"Database: {stats['database_url']}")
        print(f"Average Contract Value: ${stats['average_value']:,.2f}")
        
        if stats['contract_types']:
            print("\nContract Types:")
            for contract_type, count in stats['contract_types'].items():
                print(f"  - {contract_type}: {count}")
        
        print("=" * 40)
    
    def export_data(self, filename: str = "contracts_export.json"):
        """Export all contracts to JSON"""
        success = self.db_manager.export_to_json(filename)
        if success:
            print(f"Data exported successfully to {filename}")
        else:
            print("Export failed")
    
    def interactive_mode(self):
        """Run the application in interactive mode"""
        print("=== Contract Scanner Interactive Mode ===")
        print("Commands:")
        print("  1. Scan file")
        print("  2. Scan directory")
        print("  3. Search contracts")
        print("  4. View statistics")
        print("  5. Export data")
        print("  6. Exit")
        
        while True:
            try:
                choice = input("\nEnter command (1-6): ").strip()
                
                if choice == '1':
                    file_path = input("Enter file path: ").strip()
                    self.scan_single_file(file_path)
                
                elif choice == '2':
                    dir_path = input("Enter directory path: ").strip()
                    self.scan_directory(dir_path)
                
                elif choice == '3':
                    print("\nSearch options:")
                    print("1. By contract type")
                    print("2. By party name")
                    print("3. By text content")
                    
                    search_choice = input("Enter search option (1-3): ").strip()
                    
                    if search_choice == '1':
                        contract_type = input("Enter contract type: ").strip()
                        results = self.search_contracts(contract_type=contract_type)
                    elif search_choice == '2':
                        party_name = input("Enter party name: ").strip()
                        results = self.search_contracts(party_name=party_name)
                    elif search_choice == '3':
                        search_term = input("Enter search term: ").strip()
                        results = self.search_contracts(search_term=search_term)
                    else:
                        print("Invalid option")
                        continue
                    
                    print(f"\nFound {len(results)} contracts:")
                    for contract in results[:10]:  # Show first 10 results
                        self.display_contract_summary(contract)
                    
                    if len(results) > 10:
                        print(f"... and {len(results) - 10} more contracts")
                
                elif choice == '4':
                    self.display_statistics()
                
                elif choice == '5':
                    filename = input("Enter filename (default: contracts_export.json): ").strip()
                    if not filename:
                        filename = "contracts_export.json"
                    self.export_data(filename)
                
                elif choice == '6':
                    print("Goodbye!")
                    break
                
                else:
                    print("Invalid choice. Please enter 1-6.")
            
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error in interactive mode: {str(e)}")
                print(f"An error occurred: {str(e)}")

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Contract Scanner - Extract structured data from contracts")
    
    parser.add_argument('--file', '-f', help='Scan a single contract file')
    parser.add_argument('--directory', '-d', help='Scan all contracts in a directory')
    parser.add_argument('--database', '--db', default='sqlite:///contracts.db', 
                       help='Database URL (default: sqlite:///contracts.db)')
    parser.add_argument('--openai-key', help='OpenAI API key for enhanced analysis')
    parser.add_argument('--search', '-s', help='Search contracts by text content')
    parser.add_argument('--type', '-t', help='Search contracts by type')
    parser.add_argument('--party', '-p', help='Search contracts by party name')
    parser.add_argument('--export', '-e', help='Export contracts to JSON file')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize application
    try:
        app = ContractScannerApp(
            database_url=args.database,
            openai_api_key=args.openai_key or os.getenv('OPENAI_API_KEY')
        )
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        sys.exit(1)
    
    # Execute based on arguments
    try:
        if args.interactive:
            app.interactive_mode()
        
        elif args.file:
            app.scan_single_file(args.file)
        
        elif args.directory:
            app.scan_directory(args.directory)
        
        elif args.search:
            results = app.search_contracts(search_term=args.search)
            print(f"Found {len(results)} contracts:")
            for contract in results:
                app.display_contract_summary(contract)
        
        elif args.type:
            results = app.search_contracts(contract_type=args.type)
            print(f"Found {len(results)} contracts of type '{args.type}':")
            for contract in results:
                app.display_contract_summary(contract)
        
        elif args.party:
            results = app.search_contracts(party_name=args.party)
            print(f"Found {len(results)} contracts involving '{args.party}':")
            for contract in results:
                app.display_contract_summary(contract)
        
        elif args.export:
            app.export_data(args.export)
        
        elif args.stats:
            app.display_statistics()
        
        else:
            # No specific command, show help and enter interactive mode
            parser.print_help()
            print("\nNo specific command provided. Entering interactive mode...")
            app.interactive_mode()
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()