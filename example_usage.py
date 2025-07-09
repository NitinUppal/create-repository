#!/usr/bin/env python3
"""
Example usage script for the Contract Scanner system
This demonstrates various ways to use the contract scanning functionality
"""

import os
from pathlib import Path
from contract_scanner import ContractScanner, ContractData
from database_manager import DatabaseManager

def create_sample_contract():
    """Create a sample contract file for testing"""
    sample_contract = """
    SERVICE AGREEMENT
    
    This Service Agreement ("Agreement") is entered into on January 15, 2024,
    between TechCorp Inc., a Delaware corporation ("Company"), and 
    John Smith Consulting LLC ("Consultant").
    
    1. SCOPE OF WORK
    The Consultant agrees to provide software development services as detailed
    in Exhibit A attached hereto.
    
    2. COMPENSATION
    The Company agrees to pay the Consultant a total amount of $50,000 USD
    for the services described herein.
    
    3. TERM
    This Agreement shall commence on February 1, 2024 and shall terminate
    on August 31, 2024, unless earlier terminated in accordance with the
    provisions hereof.
    
    4. CONFIDENTIALITY
    The Consultant agrees to maintain strict confidentiality regarding all
    proprietary information disclosed by the Company.
    
    5. INTELLECTUAL PROPERTY
    All work products created under this Agreement shall be the exclusive
    property of the Company.
    
    6. TERMINATION
    Either party may terminate this Agreement with thirty (30) days written notice.
    
    7. GOVERNING LAW
    This Agreement shall be governed by the laws of the State of Delaware.
    
    IN WITNESS WHEREOF, the parties have executed this Agreement as of the
    date first written above.
    
    TechCorp Inc.                    John Smith Consulting LLC
    
    By: _________________           By: _________________
    Name: Jane Doe                  Name: John Smith
    Title: CEO                      Title: Owner
    """
    
    # Create contracts directory if it doesn't exist
    contracts_dir = Path("sample_contracts")
    contracts_dir.mkdir(exist_ok=True)
    
    # Write sample contract
    sample_file = contracts_dir / "service_agreement.txt"
    with open(sample_file, 'w') as f:
        f.write(sample_contract)
    
    print(f"Created sample contract: {sample_file}")
    return str(sample_file)

def example_single_file_scan():
    """Example: Scan a single contract file"""
    print("\n=== Example 1: Single File Scan ===")
    
    # Create sample contract
    contract_file = create_sample_contract()
    
    # Initialize scanner
    scanner = ContractScanner()
    
    # Scan the contract
    contract_data = scanner.scan_contract(contract_file)
    
    # Display results
    print(f"File: {contract_data.file_name}")
    print(f"Parties: {contract_data.parties}")
    print(f"Start Date: {contract_data.start_date}")
    print(f"End Date: {contract_data.end_date}")
    print(f"Value: {contract_data.currency} {contract_data.value}")
    print(f"Key Terms Found: {len(contract_data.key_terms)}")
    
    return contract_data

def example_database_storage():
    """Example: Store contract data in database"""
    print("\n=== Example 2: Database Storage ===")
    
    # Get contract data from previous example
    contract_data = example_single_file_scan()
    
    # Initialize database manager
    db_manager = DatabaseManager("sqlite:///example_contracts.db")
    
    # Store contract in database
    contract_id = db_manager.store_contract(contract_data)
    print(f"Stored contract with ID: {contract_id}")
    
    # Retrieve contract from database
    stored_contract = db_manager.get_contract_by_id(contract_id)
    print(f"Retrieved contract: {stored_contract.file_name}")
    
    return db_manager

def example_directory_scan():
    """Example: Scan entire directory"""
    print("\n=== Example 3: Directory Scan ===")
    
    # Create additional sample contracts
    contracts_dir = Path("sample_contracts")
    
    # Create NDA contract
    nda_content = """
    NON-DISCLOSURE AGREEMENT
    
    This Non-Disclosure Agreement is made on March 1, 2024,
    between ABC Corporation and XYZ Technologies.
    
    The parties agree to keep confidential all proprietary information
    shared during their business discussions.
    
    This agreement shall remain in effect until December 31, 2024.
    
    Payment for consulting services: $25,000 USD.
    """
    
    with open(contracts_dir / "nda_agreement.txt", 'w') as f:
        f.write(nda_content)
    
    # Initialize scanner
    scanner = ContractScanner()
    
    # Scan entire directory
    contracts = scanner.scan_directory("sample_contracts")
    
    print(f"Found {len(contracts)} contracts in directory")
    for contract in contracts:
        print(f"- {contract.file_name}: {len(contract.parties)} parties, "
              f"Value: {contract.currency or ''} {contract.value or 'N/A'}")
    
    return contracts

def example_database_queries():
    """Example: Database queries and search"""
    print("\n=== Example 4: Database Queries ===")
    
    # Scan directory and store all contracts
    contracts = example_directory_scan()
    db_manager = DatabaseManager("sqlite:///example_contracts.db")
    
    # Store all contracts
    stored_ids = db_manager.store_contracts(contracts)
    print(f"Stored {len(stored_ids)} contracts in database")
    
    # Search by party name
    results = db_manager.search_contracts("TechCorp")
    print(f"Found {len(results)} contracts containing 'TechCorp'")
    
    # Get contracts by value range
    high_value_contracts = db_manager.get_contracts_by_value_range(30000, 100000)
    print(f"Found {len(high_value_contracts)} contracts with value $30K-$100K")
    
    # Get database statistics
    stats = db_manager.get_statistics()
    print(f"Database statistics:")
    print(f"- Total contracts: {stats['total_contracts']}")
    print(f"- Average value: ${stats['average_value']:,.2f}")
    
    return db_manager

def example_data_export():
    """Example: Export data to JSON"""
    print("\n=== Example 5: Data Export ===")
    
    # Use database from previous example
    db_manager = example_database_queries()
    
    # Export to JSON
    export_file = "contracts_export_example.json"
    success = db_manager.export_to_json(export_file)
    
    if success:
        print(f"Successfully exported data to {export_file}")
        
        # Check file size
        file_size = os.path.getsize(export_file)
        print(f"Export file size: {file_size:,} bytes")
    else:
        print("Export failed")

def cleanup_example_files():
    """Clean up example files created during demonstration"""
    import shutil
    
    # Remove sample contracts directory
    if Path("sample_contracts").exists():
        shutil.rmtree("sample_contracts")
    
    # Remove database files
    for db_file in ["example_contracts.db", "contracts_export_example.json"]:
        if Path(db_file).exists():
            os.remove(db_file)
    
    print("\nCleaned up example files")

def main():
    """Run all examples"""
    print("Contract Scanner System - Example Usage")
    print("=" * 50)
    
    try:
        # Run examples
        example_single_file_scan()
        example_database_storage()
        example_directory_scan()
        example_database_queries()
        example_data_export()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
        # Ask user if they want to clean up
        response = input("\nDo you want to clean up example files? (y/n): ")
        if response.lower() in ['y', 'yes']:
            cleanup_example_files()
    
    except Exception as e:
        print(f"Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()