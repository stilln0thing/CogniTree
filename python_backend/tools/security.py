"""
security.py — Defense-in-depth security guardrails for CogniTree agent operations.
"""

import ast
import os
import re
from typing import Tuple, Optional

from python_backend.logger import setup_logger

logger = setup_logger("cognitree.tools.security")

DEFAULT_WORK_DIR = os.path.abspath(os.getenv("AGENT_WORK_DIR", "./workspace"))


def is_path_safe(target_path: str, work_dir: Optional[str] = None) -> Tuple[bool, str]:
    """
    Confines all filesystem access strictly within work_dir.
    """
    base_dir = os.path.abspath(work_dir or DEFAULT_WORK_DIR)
    
    try:
        if not os.path.isabs(target_path):
            full_path = os.path.abspath(os.path.join(base_dir, target_path))
        else:
            full_path = os.path.abspath(target_path)

        if os.path.commonpath([base_dir, full_path]) != base_dir:
            logger.warning("Security Path Jail Blocked: Target path '%s' escapes workspace base '%s'", target_path, base_dir)
            return False, f"Access Denied: Path '{target_path}' escapes workspace jail '{base_dir}'."
            
        forbidden_substrings = [".ssh", ".aws", ".env", "etc/passwd", "C:\\Windows"]
        for forbidden in forbidden_substrings:
            if forbidden.lower() in full_path.lower():
                logger.warning("Security Path Jail Blocked: System location '%s' detected in '%s'", forbidden, full_path)
                return False, f"Access Denied: System location '{forbidden}' is restricted."

        logger.info("Path security check passed for target '%s' -> resolved '%s'", target_path, full_path)
        return True, full_path
    except Exception as exc:
        logger.error("Path resolution failed for '%s': %s", target_path, str(exc))
        return False, f"Invalid path resolution: {str(exc)}"


FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__"}
FORBIDDEN_MODULES = {"ctypes", "pty", "winreg", "subprocess"}


def check_python_ast(code_str: str) -> Tuple[bool, str]:
    """
    Parses Python code into an AST to detect dangerous function calls or imports.
    """
    try:
        tree = ast.parse(code_str)
    except SyntaxError as err:
        logger.warning("AST Inspection: Python Syntax Error in code block: %s", str(err))
        return False, f"Python Syntax Error: {err}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                logger.warning("AST Inspection Blocked: Detected forbidden function call '%s()'", node.func.id)
                return False, f"Security Violation: Forbidden call '{node.func.id}()' detected."
        
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in FORBIDDEN_MODULES:
                    logger.warning("AST Inspection Blocked: Detected forbidden import '%s'", alias.name)
                    return False, f"Security Violation: Import of module '{alias.name}' is blocked."
                    
        elif isinstance(node, ast.ImportFrom):
            if node.module in FORBIDDEN_MODULES:
                logger.warning("AST Inspection Blocked: Detected forbidden import from module '%s'", node.module)
                return False, f"Security Violation: Import from module '{node.module}' is blocked."

    logger.info("AST static code inspection passed.")
    return True, "AST security check passed."


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
    redaction_count = 0
    for pattern, replacement in SECRET_PATTERNS:
        sanitized, count = pattern.subn(replacement, sanitized)
        redaction_count += count

    if redaction_count > 0:
        logger.info("DLP Secret Masking: Redacted %d credential secret pattern(s) from output.", redaction_count)

    return sanitized
