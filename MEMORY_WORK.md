# Memory Implementation Checklist

## LAYER 1 — Fix Scratchpad (Add New Tables and Query Functions)

- [x] Add memory table to backend/db/database.py
- [x] Add user_profile table to backend/db/database.py
- [x] Add save_memory function to backend/db/queries.py
- [x] Add search_memory function to backend/db/queries.py
- [x] Add upsert_user_profile function to backend/db/queries.py
- [x] Add get_all_user_profile function to backend/db/queries.py

## LAYER 2 — Fix agent.py to Use DB Scratchpad Properly

- [x] Load scratchpad from DB at task start (replace empty dict with get_scratchpad call)
- [x] Ensure scratchpad saves to DB on every update_scratchpad tool call

## LAYER 3 — Inject Long Term Memory into Every Task

- [x] Add user profile loading at start of run_agent()
- [x] Add past memory search at start of run_agent()
- [x] Add USER PROFILE section to _SYSTEM_PROMPT
- [x] Add RELEVANT PAST WORK section to _SYSTEM_PROMPT
- [x] Add USER PROFILE section to _GROQ_SYSTEM_PROMPT
- [x] Add RELEVANT PAST WORK section to _GROQ_SYSTEM_PROMPT
- [x] Update .format() calls for both system prompts to include user_profile and past_memory

## LAYER 4 — Truncate Messages and Save Memory After Task Completes

### PART A — Truncation
- [x] Wrap every tool result with truncate_result() before appending to messages

### PART B — Message Summarization After 10 Steps
- [x] Add message compression after step 10 (every 5 steps)
- [x] Implement same compression for groq_messages

### PART C — Save to Memory When Task Completes
- [x] Save to memory table when task_complete tool is called

### PART D — Learn User Profile from Task
- [x] Extract user facts after task completes via LLM call
- [x] Upsert learned facts to user_profile table

## VERIFICATION

- [x] Database initialized with new tables (memory, user_profile)
- [ ] Test 1: Submit task, check scratchpad table has rows during execution
- [ ] Test 1: Check memory table has one row after task completes
- [ ] Test 1: Check user_profile table has at least one row
- [ ] Test 2: Submit same task again, verify past memory in system prompt
- [ ] Test 3: Submit 15 step task, verify messages get compressed
- [ ] Test 3: Verify no context overflow error

## POST-IMPLEMENTATION UPDATES

- [x] Update MASTER.md — Add to Completed: 4-layer memory system
- [x] Update MASTER.md — Add to Decisions Log: memory architecture decisions
- [x] Update MASTER.md — Add two new tables to file structure section
