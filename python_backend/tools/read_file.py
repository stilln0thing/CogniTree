"""
read_file.py — Workspace-jailed file reading tool.
"""

import os
from langchain_core.tools import tool
from python_backend.tools.security import is_path_safe, sanitize_output


@tool
def read_file(filepath: str) -> str:
    """Reads the contents of a text file inside the workspace directory."""
    safe, res = is_path_safe(filepath)
    if not safe:
        return res

    if not os.path.exists(res):
        return f"Error: File '{filepath}' does not exist."

    try:
        with open(res, "r", encoding="utf-8") as f:
            content = f.read(100000) # 100 KB max limit
        return sanitize_output(content)
    except Exception as exc:
        return f"Error reading file '{filepath}': {str(exc)}"
