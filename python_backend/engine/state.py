"""
state.py — LangGraph AgentState Definition for CogniTree.
"""

from typing import Annotated, Optional, Dict, List, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Core state tracked across LangGraph node execution cycles.
    """
    # Messages list uses add_messages reducer so new messages get appended automatically
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Optional dynamic task decomposition plan
    plan: Optional[List[str]]
    
    # Active files attached to current turn
    attached_files: Dict[str, str]
    
    # Execution turn counter
    iteration: int
    
    # Stream flag
    is_streaming: bool
    
    # Two-strike self-healing recovery counter
    recovery_count: Optional[int]
    
    # List of warned function signatures to prevent duplicate broken tool calls
    warned_signatures: Optional[List[str]]
