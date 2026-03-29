import sys
sys.path.insert(0, r'C:\Users\HP\Newato\backend')

from config import settings
from utils.logger import get_logger
from utils.sanitizer import is_code_safe
from db.models import Task, Step
from tools.registry import TOOL_REGISTRY
from core.router import classify_task

# Test routing
t1 = classify_task('search for AI companies on Google')
assert t1 == 'web', f'Expected web, got {t1}'

t2 = classify_task('create a python script to process CSV')
assert t2 in ('code', 'api'), f'Unexpected: {t2}'

# Test sanitizer
safe, _ = is_code_safe('print("hello")')
assert safe, 'Safe code blocked!'

unsafe, reason = is_code_safe('import os; os.system("rm -rf /")')
assert not unsafe, f'Unsafe code passed! reason={reason}'

# Test tool count
assert len(TOOL_REGISTRY) == 13, f'Expected 13 tools, got {len(TOOL_REGISTRY)}'

print(f"PASS: router={t1}, tools={len(TOOL_REGISTRY)} registered, safety checks pass")
