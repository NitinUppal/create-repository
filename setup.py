#!/usr/bin/env python3
"""
Setup script for Contract Scanner System
This script helps install dependencies and configure the system
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(f"  Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        print(f"  Current version: {sys.version}")
        return False
    print(f"✓ Python version {sys.version.split()[0]} is compatible")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling Python dependencies...")
    
    # Check if pip is available
    if not shutil.which('pip'):
        print("✗ pip is not available. Please install pip first.")
        return False
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        return False
    
    return True

def install_spacy_model():
    """Install spaCy language model"""
    print("\nInstalling spaCy language model...")
    
    # Try to install en_core_web_sm model
    if not run_command("python -m spacy download en_core_web_sm", "Installing spaCy English model"):
        print("⚠ spaCy model installation failed. NLP features may be limited.")
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    
    directories = [
        "contracts",
        "output",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    return True

def setup_environment_file():
    """Set up environment file"""
    print("\nSetting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_example.exists() and not env_file.exists():
        shutil.copy(env_example, env_file)
        print("✓ Created .env file from template")
        print("  Please edit .env file to configure your settings")
    elif env_file.exists():
        print("✓ .env file already exists")
    else:
        print("⚠ .env.example not found, creating basic .env file")
        with open(env_file, 'w') as f:
            f.write("# Contract Scanner Configuration\n")
            f.write("DATABASE_URL=sqlite:///contracts.db\n")
            f.write("LOG_LEVEL=INFO\n")
            f.write("# OPENAI_API_KEY=your_key_here\n")
        print("✓ Created basic .env file")
    
    return True

def test_installation():
    """Test if the installation works"""
    print("\nTesting installation...")
    
    try:
        # Try importing main modules
        from contract_scanner import ContractScanner
        from database_manager import DatabaseManager
        print("✓ Core modules import successfully")
        
        # Test basic functionality
        scanner = ContractScanner()
        db_manager = DatabaseManager("sqlite:///:memory:")
        print("✓ Core classes initialize successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Initialization error: {e}")
        return False

def show_usage_examples():
    """Show usage examples"""
    print("\n" + "="*60)
    print("SETUP COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\nQuick Start Examples:")
    print("\n1. Interactive Mode:")
    print("   python main.py --interactive")
    
    print("\n2. Scan a single file:")
    print("   python main.py --file path/to/contract.pdf")
    
    print("\n3. Scan a directory:")
    print("   python main.py --directory ./contracts/")
    
    print("\n4. Run example demonstration:")
    print("   python example_usage.py")
    
    print("\n5. View help:")
    print("   python main.py --help")
    
    print("\nConfiguration:")
    print("- Edit .env file for database and API settings")
    print("- Check contract_scanner_README.md for detailed documentation")
    print("- Logs will be saved to contract_scanner.log")
    
    print("\nNext Steps:")
    print("1. Place contract files in the 'contracts' directory")
    print("2. Run: python main.py --directory contracts")
    print("3. View results: python main.py --stats")

def main():
    """Main setup function"""
    print("Contract Scanner System Setup")
    print("="*40)
    
    # Track setup success
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install dependencies
    if success and not install_dependencies():
        success = False
    
    # Install spaCy model (optional)
    if success:
        install_spacy_model()  # Don't fail setup if this fails
    
    # Create directories
    if success and not create_directories():
        success = False
    
    # Setup environment file
    if success and not setup_environment_file():
        success = False
    
    # Test installation
    if success and not test_installation():
        success = False
    
    if success:
        show_usage_examples()
    else:
        print("\n" + "="*60)
        print("SETUP FAILED")
        print("="*60)
        print("\nPlease resolve the above errors and run setup again.")
        print("You may need to:")
        print("- Update Python to version 3.8 or higher")
        print("- Install pip if not available")
        print("- Check internet connection for downloading packages")
        print("- Run with administrator privileges if needed")
        sys.exit(1)

if __name__ == "__main__":
    main()