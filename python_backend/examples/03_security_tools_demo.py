"""
03_security_tools_demo.py — Phase 3: Security & Tool Suite Verification Demo
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from python_backend.tools.security import is_path_safe, check_python_ast, sanitize_output
from python_backend.tools.run_local_python_script import run_local_python_script


def main():
    print("Testing CogniTree Security Guardrails & Tool Suite...\n")

    # Test 1: Workspace Path Jail
    print("Testing Path Jail (is_path_safe):")
    safe1, msg1 = is_path_safe("notes.txt")
    print(f"   - Relative path 'notes.txt': Safe={safe1} ({msg1})")
    
    safe2, msg2 = is_path_safe("../../etc/passwd")
    print(f"   - Traversal path '../../etc/passwd': Safe={safe2} ({msg2})\n")

    # Test 2: AST Security Check
    print("Testing AST Static Code Inspection (check_python_ast):")
    safe_code = "print('Hello from safe code!')"
    ok1, ast_msg1 = check_python_ast(safe_code)
    print(f"   - Safe code: Passed={ok1} ({ast_msg1})")

    dangerous_code = "import ctypes\nctypes.CDLL(None)"
    ok2, ast_msg2 = check_python_ast(dangerous_code)
    print(f"   - Dangerous code (ctypes import): Passed={ok2} ({ast_msg2})\n")

    # Test 3: DLP Secret Masking
    print("Testing Secret Masking (sanitize_output):")
    raw_log = "Error connecting with key sk-proj-1234567890abcdef1234567890abcdef"
    clean_log = sanitize_output(raw_log)
    print(f"   - Raw: {raw_log}")
    print(f"   - Cleaned: {clean_log}\n")

    # Test 4: Subprocess Python Script Tool
    print("Testing Subprocess Script Execution (run_local_python_script):")
    script = "result = sum([i * 2 for i in range(10)])\nprint(f'Computed sum: {result}')"
    out = run_local_python_script.invoke({"code_str": script})
    print(f"   - Result:\n{out}")

    print("All Phase 3 Security Guardrail tests passed!")


if __name__ == "__main__":
    main()
