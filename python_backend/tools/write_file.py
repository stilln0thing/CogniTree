"""
write_file.py — Workspace-jailed file writing tool.
"""

import os
from langchain_core.tools import tool
from python_backend.tools.security import is_path_safe


@tool
def write_file(filepath: str, content: str) -> str:
    """Writes or overwrites text content to a file inside the workspace directory."""
    safe, res = is_path_safe(filepath)
    if not safe:
        return res

    try:
        os.makedirs(os.path.dirname(res), exist_ok=True)
        with open(res, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} bytes to '{filepath}'."
    except Exception as exc:
        return f"Error writing file '{filepath}': {str(exc)}"
