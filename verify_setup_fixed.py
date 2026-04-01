#!/usr/bin/env python3
"""
Quick Setup Verification Script
Tests if the setup completed successfully before running start-dev.ps1
"""

import sys
import subprocess
from pathlib import Path
import time

def check_item(name, condition, details=""):
    status = "✅" if condition else "❌"
    print(f"{status} {name}")
    if details and not condition:
        print(f"   └─ {details}")
    return condition

def main():
    print("🔍 ARIA Setup Verification")
    print("=" * 40)
    
    root = Path(__file__).parent
    backend_dir = root / "backend"
    
    all_good = True
    
    # Check virtual environment
    venv_python = backend_dir / "venv" / "Scripts" / "python.exe"
    all_good &= check_item("Virtual environment", venv_python.exists(), 
                          "Run: .\\scripts\\setup.ps1")
    
    # Check .env file
    env_file = root / ".env"
    all_good &= check_item(".env file exists", env_file.exists(),
                          "Run: .\\scripts\\setup.ps1")
    
    # Check node_modules
    electron_modules = root / "electron" / "node_modules"
    frontend_modules = root / "frontend" / "node_modules"
    all_good &= check_item("Electron dependencies", electron_modules.exists(),
                          "Run: .\\scripts\\setup.ps1")
    all_good &= check_item("Frontend dependencies", frontend_modules.exists(),
                          "Run: .\\scripts\\setup.ps1")
    
    if not all_good:
        print("\n❌ Setup incomplete. Run: .\\scripts\\setup.ps1")
        return False
    
    print("\n🎉 Setup verification PASSED!")
    print("Ready to run: .\\scripts\\start-dev.ps1")
    
    # Check .env has API key
    if env_file.exists():
        env_content = env_file.read_text()
        if "your_groq_key_here" in env_content or "your_anthropic_key_here" in env_content:
            print("\n⚠️  REMINDER: Edit .env file and add your API key!")
            print("   Get free Groq key: https://console.groq.com")
    
    return True

if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)