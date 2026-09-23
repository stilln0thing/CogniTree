"""
security.py — Defense-in-depth security guardrails for CogniTree agent operations.
"""

import ast
import os
import re
from typing import Tuple, Optional

# Default fallback working directory
DEFAULT_WORK_DIR = os.path.abspath(os.getenv("AGENT_WORK_DIR", "./workspace"))


# ── 1. Workspace Path Jailing ─────────────────────────────────────────────────

def is_path_safe(target_path: str, work_dir: Optional[str] = None) -> Tuple[bool, str]:
    """
    Confines all filesystem access strictly within work_dir.
    Blocks directory traversal ('../'), absolute path escapes, and system directory accesses.
    """
    base_dir = os.path.abspath(work_dir or DEFAULT_WORK_DIR)
    
    try:
        # Resolve target path relative to base directory
        if not os.path.isabs(target_path):
            full_path = os.path.abspath(os.path.join(base_dir, target_path))
        else:
            full_path = os.path.abspath(target_path)

        # Ensure full_path starts with base_dir prefix
        if os.path.commonpath([base_dir, full_path]) != base_dir:
            return False, f"Access Denied: Path '{target_path}' escapes workspace jail '{base_dir}'."
            
        # Unconditional blocklist for sensitive system locations
        forbidden_substrings = [".ssh", ".aws", ".env", "etc/passwd", "C:\\Windows"]
        for forbidden in forbidden_substrings:
            if forbidden.lower() in full_path.lower():
                return False, f"Access Denied: System location '{forbidden}' is restricted."

        return True, full_path
    except Exception as exc:
        return False, f"Invalid path resolution: {str(exc)}"


# ── 2. AST Static Code Inspection ─────────────────────────────────────────────

FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__"}
FORBIDDEN_MODULES = {"ctypes", "pty", "winreg", "subprocess"}


def check_python_ast(code_str: str) -> Tuple[bool, str]:
    """
    Parses Python code into an Abstract Syntax Tree (AST) to detect dangerous calls
    or forbidden imports prior to execution.
    """
    try:
        tree = ast.parse(code_str)
    except SyntaxError as err:
        return False, f"Python Syntax Error: {err}"

    for node in ast.walk(tree):
        # Check forbidden function calls
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                return False, f"Security Violation: Forbidden call '{node.func.id}()' detected."
        
        # Check forbidden imports
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in FORBIDDEN_MODULES:
                    return False, f"Security Violation: Import of module '{alias.name}' is blocked."
                    
        elif isinstance(node, ast.ImportFrom):
            if node.module in FORBIDDEN_MODULES:
                return False, f"Security Violation: Import from module '{node.module}' is blocked."

    return True, "AST security check passed."


# ── 3. DLP Secret Masking ─────────────────────────────────────────────────────

SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9]{32,}", re.IGNORECASE), "[REDACTED_OPENAI_KEY]"),
    (re.compile(r"ghp_[a-zA-Z0-9]{36}", re.IGNORECASE), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE), "[REDACTED_AWS_KEY]"),
    (re.compile(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]")
]


def sanitize_output(text: str) -> str:
    """
    Redacts sensitive credentials and secret keys from tool output text.
    """
    if not isinstance(text, str):
        return text

    sanitized = text
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    return sanitized
