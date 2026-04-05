# TODAYS_WORK.md — Session Checklist

**Session Start:** 2025-01-XX
**Goal:** Fix critical bugs + implement memory system + verify end-to-end

---

## Critical Fixes (do these first, in order)

- [x] Fix port mismatch — frontend and backend must connect
  - Changed .env ARIA_WEBSOCKET_PORT to 8765 (both root and backend/.env)
  - Verified backend config.py reads port 8765 correctly
  - Frontend already hardcodes ws://127.0.0.1:8765/ws - now matches

- [x] Fix setOutputDir crash — fires on every WebSocket connection
  - Added outputDir: null to taskStore.js initial state (already existed)
  - Added setOutputDir: (dir) => set({ outputDir: dir }) action to taskStore.js
  - Added setOutputDir to destructured actions in useWebSocket.js
  - Added setOutputDir to useCallback dependency array

- [x] Fix write_file handle leak — causes PermissionError on Windows
  - Replaced file_path.open("a").write() with proper context manager (with statement)
  - Now uses: with file_path.open("a", encoding="utf-8") as f: f.write(content)
  - File handle is properly closed after write

- [x] Fix white screen flash on overlay window
  - Added isReady state with 50ms delay to ensure CSS loads before showing
  - Added backgroundColor: '#00000000' to Electron overlay window config
  - Added opacity control to prevent white flash during initial render
  - Overlay now fades in smoothly without white background

- [ ] Verify all 3 fixes work together — app starts, frontend connects, task submits without crash
  - NEEDS TESTING: Start full app with .\scripts\start-dev.ps1
  - NEEDS TESTING: Press Ctrl+Shift+Space
  - NEEDS TESTING: Submit: "Go to example.com and save the page title to fix_test.txt"
  - NEEDS TESTING: Verify task card appears, steps update live, file exists in outputs folder

---

## Memory Implementation

- [x] Scratchpad is actively written during agent loop
  - Added await queries.get_scratchpad(db, task_id) at agent start to load existing scratchpad
  - Scratchpad is passed in tool_context to all tools
  - upsert_scratchpad() is called when update_scratchpad tool is used (already existed)
  - Scratchpad persists to SQLite scratchpad table

- [x] Scratchpad is read and injected into every LLM prompt
  - Format scratchpad as "key: value\n" string (more readable than JSON)
  - Inject into system prompt via {scratchpad} placeholder
  - System prompt rebuilt on every loop iteration with current scratchpad state
  - LLM can reference scratchpad data in subsequent steps

- [x] Tool results are truncated before going into message history
  - truncate_result() already exists in sanitizer.py
  - Already being used in agent.py for all tool results
  - Increased limit from 1000 to 2000 chars as specified
  - Prevents large HTML pages from overflowing context

- [x] Message history is summarized after 10 steps
  - Added summarization logic for both Anthropic and Groq/OpenAI message arrays
  - Triggers when messages > 12 (Anthropic) or > 13 (Groq with system msg)
  - Keeps last 4 messages intact (most recent context)
  - Summarizes old messages as "Previous steps: - Used tool_name" list
  - Replaces old messages with single summary message
  - Logs summarization event with old/new message counts

- [ ] Memory works across a full 10+ step task without context overflow
  - NEEDS TESTING: Submit complex multi-step task (10-15 steps)
  - NEEDS TESTING: Monitor SQLite scratchpad table during execution
  - NEEDS TESTING: Verify task completes without context errors
  - NEEDS TESTING: Verify output files contain real data

---

## Verification Tests

- [ ] Test 1 — app starts with no errors in terminal
  - NEEDS TESTING: Run .\scripts\start-dev.ps1
  - Check all 3 processes start (backend, frontend, electron)
  - Verify no red error messages in terminal

- [ ] Test 2 — frontend connects to backend (WebSocket shows connected)
  - Open browser devtools console
  - Look for "[ARIA WS] Connected" message
  - Verify no connection errors

- [ ] Test 3 — submit task, task card appears in sidebar
  - Press Ctrl+Shift+Space
  - Type any simple task
  - Press Enter
  - Verify task card appears in sidebar with "running" status

- [ ] Test 4 — agent completes "go to example.com, save title to test.txt"
  - Submit exact task: "Go to example.com and save the page title to test.txt"
  - Wait for completion
  - Verify test.txt exists in outputs folder
  - Verify file contains "Example Domain"

- [ ] Test 5 — file exists in outputs folder with real content
  - Navigate to ~/ARIA/outputs/[task_id]/
  - Open test.txt
  - Verify content is not empty or placeholder

- [ ] Test 6 — run a 5+ step task, verify scratchpad entries in SQLite
  - Submit: "Search for top 3 AI companies, visit each website, save taglines to ai_companies.json"
  - While running, query SQLite: SELECT * FROM scratchpad
  - Verify rows are being written during task execution
  - Verify final JSON file has real data

- [ ] Test 7 — submit 2 tasks at once, both complete with separate files
  - Submit task 1: "Go to google.com, save title to google.txt"
  - Immediately submit task 2: "Go to github.com, save title to github.txt"
  - Verify both show "running" simultaneously
  - Verify both complete with separate files in separate task_id folders

---

## Documentation Updates

- [ ] Update TODAYS_WORK.md with completion notes
  - Write what was done for each item
  - Write how it was verified
  - Note any issues encountered and how they were resolved

- [ ] Update MASTER.md
  - Remove port mismatch from Known Issues
  - Remove setOutputDir crash from Known Issues
  - Remove file handle leak from Known Issues
  - Add to Decisions Log: memory implementation details
  - Update Current Status section
  - Add to Completed section: memory system, critical bug fixes

- [ ] Run demo script from MASTER.md Section 14
  - Follow exact steps from demo script
  - If passes: write "DEMO PASSING" at top with timestamp
  - If fails: write exact failure point and reason

---

## Session End Checklist

- [ ] All critical fixes verified working
- [ ] Memory system implemented and tested
- [ ] All verification tests passing
- [ ] Both TODAYS_WORK.md and MASTER.md updated
- [ ] Demo script runs perfectly at least once

---

**Notes:**
- Check items ONLY after verification, not after writing code
- If stuck > 30 min on any item, document the blocker
- Do not skip ahead — complete in exact order listed
