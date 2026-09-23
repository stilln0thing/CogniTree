"""
run_local_python_script.py — Subprocess Python code execution tool with AST security checks.
"""

import sys
import subprocess
from langchain_core.tools import tool
from python_backend.tools.security import check_python_ast, sanitize_output


@tool
def run_local_python_script(code_str: str, timeout_seconds: int = 10) -> str:
    """
    Executes Python code in a safe subprocess after AST security inspection.
    """
    # Step 1: Pre-execution AST Security Inspection
    safe, msg = check_python_ast(code_str)
    if not safe:
        return f"AST Security Check Failed: {msg}"

    # Step 2: Execute code in isolated subprocess
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code_str],
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        
        output = ""
        if proc.stdout:
            output += f"STDOUT:\n{proc.stdout}\n"
        if proc.stderr:
            output += f"STDERR:\n{proc.stderr}\n"
        if proc.returncode != 0:
            output += f"Process exited with code {proc.returncode}"

        return sanitize_output(output or "Script executed with no output.")

    except subprocess.TimeoutExpired:
        return f"Execution Error: Script timed out after {timeout_seconds} seconds."
    except Exception as exc:
        return f"Execution Error: {str(exc)}"
