#!/usr/bin/env python3
"""
ARIA System Checklist - Quick verification of all components
"""

import subprocess
import requests
import sqlite3
from pathlib import Path
import json

def check_item(name, condition, details=""):
    status = "✅" if condition else "❌"
    print(f"{status} {name}")
    if details:
        print(f"   └─ {details}")
    return condition

def main():
    print("🔍 ARIA System Checklist")
    print("=" * 40)
    
    all_good = True
    
    # 1. Files exist
    print("\n📁 File Structure:")
    all_good &= check_item("Backend core exists", Path("backend/core/agent.py").exists())
    all_good &= check_item("Tools directory exists", Path("backend/tools").exists())
    all_good &= check_item("Database module exists", Path("backend/db/database.py").exists())
    all_good &= check_item("Electron main exists", Path("electron/main.js").exists())
    all_good &= check_item("Frontend exists", Path("frontend/src").exists())
    all_good &= check_item("Setup script exists", Path("scripts/setup.ps1").exists())
    all_good &= check_item("Dev script exists", Path("scripts/start-dev.ps1").exists())
    
    # 2. Backend running
    print("\n🖥️  Backend Status:")
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        backend_ok = response.status_code == 200
        all_good &= check_item("Backend responding", backend_ok, f"Status: {response.status_code}")
    except:
        all_good &= check_item("Backend responding", False, "Not accessible")
        backend_ok = False
    
    # 3. Database
    print("\n🗄️  Database:")
    db_path = Path("backend/db/tasks.db")
    db_exists = db_path.exists()
    all_good &= check_item("Database file exists", db_exists)
    
    if db_exists:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks")
            task_count = cursor.fetchone()[0]
            conn.close()
            all_good &= check_item("Database accessible", True, f"{task_count} tasks in DB")
        except:
            all_good &= check_item("Database accessible", False, "Cannot query")
    
    # 4. Tools (if backend is running)
    if backend_ok:
        print("\n🛠️  Tools:")
        try:
            # Test a simple tool
            tool_response = requests.post(
                "http://localhost:8000/tools/execute",
                json={"tool": "run_python", "code": "print('test')"},
                timeout=10
            )
            tools_ok = tool_response.status_code == 200
            all_good &= check_item("Tools responding", tools_ok)
        except:
            all_good &= check_item("Tools responding", False, "Tool execution failed")
    
    # 5. Processes
    print("\n⚙️  Processes:")
    try:
        # Check for Python backend
        result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe"], 
                              capture_output=True, text=True, shell=True)
        python_running = "python.exe" in result.stdout
        all_good &= check_item("Python backend process", python_running)
        
        # Check for Electron
        result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq electron.exe"], 
                              capture_output=True, text=True, shell=True)
        electron_running = "electron.exe" in result.stdout
        all_good &= check_item("Electron process", electron_running)
        
        # Check for Node (frontend dev server)
        result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq node.exe"], 
                              capture_output=True, text=True, shell=True)
        node_running = "node.exe" in result.stdout
        all_good &= check_item("Node.js process", node_running)
        
    except:
        all_good &= check_item("Process check", False, "Cannot check processes")
    
    # Summary
    print("\n" + "=" * 40)
    if all_good:
        print("🎉 All systems GO! Ready for testing.")
        print("\n💡 Quick tests you can run:")
        print("   • python test_chrome.py")
        print("   • python test_bare_minimum.py")
    else:
        print("⚠️  Some issues detected. Fix them first:")
        print("   • Run: .\\scripts\\start-dev.ps1")
        print("   • Check if all dependencies are installed")
        print("   • Verify .env file has correct settings")

if __name__ == "__main__":
    main()