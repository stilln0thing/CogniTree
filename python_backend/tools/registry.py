"""
registry.py — Tool registry and OpenAI tool schema exporter.
"""

import json
from typing import Dict, Any, List
from python_backend.tools.read_file import read_file
from python_backend.tools.write_file import write_file
from python_backend.tools.web_search import web_search
from python_backend.tools.run_local_python_script import run_local_python_script


# Available tool mapping
TOOL_MAP = {
    "read_file": read_file,
    "write_file": write_file,
    "web_search": web_search,
    "run_local_python_script": run_local_python_script
}

# OpenAI Tool Schemas passed to model
OPENAI_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads text file content inside the workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Relative path to file in workspace."}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes text content to a file inside the workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Relative path to file in workspace."},
                    "content": {"type": "string", "description": "Text content to write."}
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Performs a live web search using DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query string."},
                    "max_results": {"type": "integer", "description": "Number of results to return (default 5)."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_local_python_script",
            "description": "Executes Python code in a safe subprocess after AST inspection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code_str": {"type": "string", "description": "Python code to execute."}
                },
                "required": ["code_str"]
            }
        }
    }
]


def execute_tool_by_name(name: str, args: Dict[str, Any]) -> str:
    """Dispatches tool execution by name and returns string output."""
    tool_func = TOOL_MAP.get(name)
    if not tool_func:
        return f"Error: Tool '{name}' is not registered."

    try:
        return tool_func.invoke(args)
    except Exception as exc:
        return f"Error executing tool '{name}': {str(exc)}"
