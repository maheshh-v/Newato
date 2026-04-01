#!/usr/bin/env python3
"""
Quick Chrome Test - Validates the working "open chrome" functionality
"""

import requests
import json
import time

def test_chrome_task():
    """Test the exact 'open chrome' task that you mentioned works"""
    
    print("🧪 Testing 'open chrome' task...")
    
    try:
        # Create the task
        task_data = {
            "description": "open chrome",
            "priority": "normal"
        }
        
        print("📝 Creating task...")
        response = requests.post("http://localhost:8000/tasks", json=task_data, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Task creation failed: HTTP {response.status_code}")
            return False
            
        task_result = response.json()
        task_id = task_result.get("task_id")
        print(f"✅ Task created with ID: {task_id}")
        
        # Monitor task progress
        print("👀 Monitoring task progress...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                status_response = requests.get(f"http://localhost:8000/tasks/{task_id}")
                if status_response.status_code == 200:
                    task_info = status_response.json()
                    status = task_info.get("status", "unknown")
                    steps = task_info.get("steps", [])
                    
                    print(f"📊 Status: {status}, Steps: {len(steps)}")
                    
                    if status in ["completed", "failed"]:
                        print(f"🏁 Task finished with status: {status}")
                        
                        if steps:
                            print("📋 Steps taken:")
                            for step in steps[-3:]:  # Show last 3 steps
                                print(f"   • {step.get('action', 'Unknown')}: {step.get('result', 'No result')}")
                        
                        return status == "completed"
                        
                time.sleep(1)
            except Exception as e:
                print(f"⚠️  Error checking status: {e}")
                
        print("⏰ Task monitoring timed out")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ARIA Chrome Test")
    print("=" * 30)
    
    # Check if backend is running
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Backend not healthy. Run: .\\scripts\\start-dev.ps1")
            exit(1)
        print("✅ Backend is running")
    except:
        print("❌ Backend not accessible. Run: .\\scripts\\start-dev.ps1")
        exit(1)
    
    # Run the chrome test
    success = test_chrome_task()
    
    if success:
        print("\n🎉 Chrome test PASSED! The basic ReAct loop is working.")
    else:
        print("\n❌ Chrome test FAILED. Check the backend logs for details.")