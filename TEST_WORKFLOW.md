# ARIA User Testing Workflow

## Step 1: Fresh Setup
```powershell
.\scripts\setup.ps1
```
**Expected**: All dependencies install without errors

## Step 2: Start Development
```powershell
.\scripts\start-dev.ps1
```
**Expected**: 
- Python backend starts (port 8000)
- React frontend starts (port 3000) 
- Electron app opens
- System tray icon appears

## Step 3: Test Global Shortcut
1. Press `Ctrl+Shift+Space` from anywhere
2. **Expected**: Overlay window opens

## Step 4: Test Basic Task
1. Type: "open chrome"
2. Press Enter
3. **Expected**: 
   - Task card appears immediately
   - Chrome browser opens
   - Task shows "completed" status

## Step 5: Test Task Tracking
1. Look at the task card
2. **Expected**:
   - Shows live step updates
   - Final status is "done" (green)
   - Can click to expand full log

## Step 6: Test File Task
1. Press `Ctrl+Shift+Space`
2. Type: "create a file called test.txt with hello world"
3. Press Enter
4. **Expected**:
   - Task completes
   - File appears on desktop/current folder
   - Task shows clickable file link

## Step 7: Test Error Handling
1. Press `Ctrl+Shift+Space` 
2. Type: "navigate to invalid-website-that-doesnt-exist.com"
3. Press Enter
4. **Expected**:
   - Task tries and fails gracefully
   - Shows clear error message
   - Status shows "failed" (red)

## Step 8: Test Parallel Tasks
1. Quickly create 3 tasks:
   - "open notepad"
   - "open calculator" 
   - "create file test2.txt"
2. **Expected**:
   - All 3 tasks appear in UI
   - All run simultaneously 
   - No blocking/freezing

## Step 9: Test System Tray
1. Close main window
2. **Expected**: App stays in system tray
3. Right-click tray icon
4. **Expected**: Context menu with options

## Step 10: Test Persistence
1. Close entire app
2. Restart with `.\scripts\start-dev.ps1`
3. **Expected**: Previous tasks still visible in history

---

## 🐛 When Something Breaks:
1. Note the exact step number
2. Copy any error messages
3. Tell me: "Step X failed: [error message]"
4. I'll fix it completely

## ✅ Success Criteria:
- All 10 steps work without crashes
- Tasks complete end-to-end
- UI updates live
- No silent failures