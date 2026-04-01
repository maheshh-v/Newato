#!/usr/bin/env python3
"""
ARIA Bare Minimum Testing Script
Tests all core functionality to ensure the system works end-to-end
"""

import asyncio
import json
import sqlite3
import subprocess
import time
import requests
import websockets
from pathlib import Path
import tempfile
import os
import sys

class ARIATestSuite:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000/ws"
        self.db_path = Path("backend/db/tasks.db")
        self.results = []
        
    def log(self, test_name, status, message=""):
        result = f"{'✓' if status else '✗'} {test_name}: {message}"
        print(result)
        self.results.append((test_name, status, message))
        
    def check_backend_running(self):
        """Test: Backend is accessible"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            self.log("Backend Health Check", response.status_code == 200, f"Status: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log("Backend Health Check", False, f"Error: {str(e)}")
            return False
            
    def test_database_connection(self):
        """Test: SQLite database exists and is accessible"""
        try:
            if not self.db_path.exists():
                self.log("Database File", False, "tasks.db not found")
                return False
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            has_tasks = any('tasks' in str(table) for table in tables)
            self.log("Database Connection", True, f"Tables: {len(tables)}, Has tasks: {has_tasks}")
            return True
        except Exception as e:
            self.log("Database Connection", False, f"Error: {str(e)}")
            return False
            
    def test_task_creation(self):
        """Test: Task saves to SQLite when created"""
        try:
            task_data = {
                "description": "Test task - open chrome",
                "priority": "normal"
            }
            
            response = requests.post(f"{self.base_url}/tasks", json=task_data, timeout=10)
            
            if response.status_code == 200:
                task_id = response.json().get("task_id")
                self.log("Task Creation", True, f"Created task {task_id}")
                return task_id
            else:
                self.log("Task Creation", False, f"HTTP {response.status_code}")
                return None
        except Exception as e:
            self.log("Task Creation", False, f"Error: {str(e)}")
            return None
            
    def test_task_persistence(self, task_id):
        """Test: Task is saved in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()
            conn.close()
            
            exists = task is not None
            self.log("Task Persistence", exists, f"Task {task_id} in DB: {exists}")
            return exists
        except Exception as e:
            self.log("Task Persistence", False, f"Error: {str(e)}")
            return False
            
    async def test_websocket_connection(self):
        """Test: WebSocket connection for live updates"""
        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Send a ping or test message
                await websocket.send(json.dumps({"type": "ping"}))
                
                # Wait for response with timeout
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                self.log("WebSocket Connection", True, "Connected and responsive")
                return True
        except Exception as e:
            self.log("WebSocket Connection", False, f"Error: {str(e)}")
            return False
            
    def test_browser_tool(self):
        """Test: Browser navigate tool works"""
        try:
            # Test browser_navigate tool directly
            tool_data = {
                "tool": "browser_navigate",
                "url": "https://www.google.com"
            }
            
            response = requests.post(f"{self.base_url}/tools/execute", json=tool_data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                success = result.get("success", False)
                self.log("Browser Navigate Tool", success, f"Result: {result.get('message', '')}")
                return success
            else:
                self.log("Browser Navigate Tool", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log("Browser Navigate Tool", False, f"Error: {str(e)}")
            return False
            
    def test_file_tool(self):
        """Test: Write file tool works"""
        try:
            test_file = Path(tempfile.gettempdir()) / "aria_test.txt"
            tool_data = {
                "tool": "write_file",
                "path": str(test_file),
                "content": "ARIA test file - created by test suite"
            }
            
            response = requests.post(f"{self.base_url}/tools/execute", json=tool_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                success = result.get("success", False) and test_file.exists()
                
                # Clean up
                if test_file.exists():
                    test_file.unlink()
                    
                self.log("Write File Tool", success, f"File created and cleaned up")
                return success
            else:
                self.log("Write File Tool", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log("Write File Tool", False, f"Error: {str(e)}")
            return False
            
    def test_python_tool(self):
        """Test: Python execution tool works"""
        try:
            tool_data = {
                "tool": "run_python",
                "code": "print('Hello from ARIA test'); result = 2 + 2; print(f'2 + 2 = {result}')"
            }
            
            response = requests.post(f"{self.base_url}/tools/execute", json=tool_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                success = result.get("success", False)
                output = result.get("output", "")
                has_expected = "Hello from ARIA test" in output and "2 + 2 = 4" in output
                
                self.log("Python Execution Tool", success and has_expected, f"Output contains expected text: {has_expected}")
                return success and has_expected
            else:
                self.log("Python Execution Tool", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log("Python Execution Tool", False, f"Error: {str(e)}")
            return False
            
    def test_error_handling(self):
        """Test: Tools return clear error messages"""
        try:
            # Test with invalid tool
            tool_data = {
                "tool": "invalid_tool",
                "param": "test"
            }
            
            response = requests.post(f"{self.base_url}/tools/execute", json=tool_data, timeout=10)
            
            if response.status_code in [400, 404]:
                result = response.json()
                has_error_msg = "error" in result or "message" in result
                self.log("Error Handling", has_error_msg, f"Returns clear error message")
                return has_error_msg
            else:
                self.log("Error Handling", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log("Error Handling", False, f"Error: {str(e)}")
            return False
            
    def test_parallel_tasks(self):
        """Test: Multiple tasks can be created without blocking"""
        try:
            import threading
            import time
            
            results = []
            
            def create_task(task_num):
                try:
                    task_data = {
                        "description": f"Parallel test task {task_num}",
                        "priority": "normal"
                    }
                    start_time = time.time()
                    response = requests.post(f"{self.base_url}/tasks", json=task_data, timeout=10)
                    end_time = time.time()
                    
                    results.append({
                        "task_num": task_num,
                        "success": response.status_code == 200,
                        "duration": end_time - start_time,
                        "task_id": response.json().get("task_id") if response.status_code == 200 else None
                    })
                except Exception as e:
                    results.append({
                        "task_num": task_num,
                        "success": False,
                        "error": str(e)
                    })
            
            # Create 3 tasks in parallel
            threads = []
            for i in range(3):
                thread = threading.Thread(target=create_task, args=(i+1,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            successful_tasks = sum(1 for r in results if r.get("success", False))
            avg_duration = sum(r.get("duration", 0) for r in results if "duration" in r) / len(results)
            
            success = successful_tasks == 3 and avg_duration < 5.0
            self.log("Parallel Tasks", success, f"{successful_tasks}/3 tasks created, avg {avg_duration:.2f}s")
            return success
            
        except Exception as e:
            self.log("Parallel Tasks", False, f"Error: {str(e)}")
            return False
            
    def check_electron_process(self):
        """Test: Check if Electron app is running"""
        try:
            # Check for electron process
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq electron.exe"],
                capture_output=True,
                text=True,
                shell=True
            )
            
            electron_running = "electron.exe" in result.stdout
            self.log("Electron Process", electron_running, f"Electron app running: {electron_running}")
            return electron_running
        except Exception as e:
            self.log("Electron Process", False, f"Error: {str(e)}")
            return False
            
    def check_setup_scripts(self):
        """Test: Setup scripts exist and are executable"""
        setup_script = Path("scripts/setup.ps1")
        dev_script = Path("scripts/start-dev.ps1")
        
        setup_exists = setup_script.exists()
        dev_exists = dev_script.exists()
        
        self.log("Setup Scripts", setup_exists and dev_exists, 
                f"setup.ps1: {setup_exists}, start-dev.ps1: {dev_exists}")
        
        return setup_exists and dev_exists
        
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting ARIA Bare Minimum Test Suite")
        print("=" * 50)
        
        # Core infrastructure tests
        backend_ok = self.check_backend_running()
        if not backend_ok:
            print("❌ Backend not running. Start with: .\\scripts\\start-dev.ps1")
            return False
            
        self.test_database_connection()
        await self.test_websocket_connection()
        
        # Task management tests
        task_id = self.test_task_creation()
        if task_id:
            self.test_task_persistence(task_id)
            
        # Tool tests
        self.test_browser_tool()
        self.test_file_tool()
        self.test_python_tool()
        self.test_error_handling()
        
        # Advanced tests
        self.test_parallel_tasks()
        
        # System tests
        self.check_electron_process()
        self.check_setup_scripts()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        
        passed = sum(1 for _, status, _ in self.results if status)
        total = len(self.results)
        
        for test_name, status, message in self.results:
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {test_name}")
            if message and not status:
                print(f"   └─ {message}")
                
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All bare minimum requirements are working!")
        else:
            print("⚠️  Some requirements need attention. Check the Code Issues panel for details.")
            
        return passed == total

if __name__ == "__main__":
    suite = ARIATestSuite()
    success = asyncio.run(suite.run_all_tests())
    sys.exit(0 if success else 1)