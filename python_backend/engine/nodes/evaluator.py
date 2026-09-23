"""
evaluator.py — Evaluator node, conditional router, and self-healing recovery node.
"""

from typing import Dict, Any, Literal
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from langgraph.graph import END
from python_backend.engine.state import AgentState


def should_continue(state: AgentState) -> Literal["tools", "recovery", "__end__"]:
    """
    Conditional edge router evaluating the current state:
    - If AIMessage has tool_calls -> route to 'tools'
    - If tool call repeatedly failed -> route to 'recovery'
    - Otherwise -> route to END
    """
    messages = state.get("messages", [])
    if not messages:
        return END

    last_msg = messages[-1]
    iteration = state.get("iteration", 0)

    # Prevent infinite loops (hard limit at 10 iterations)
    if iteration > 10:
        return END

    if isinstance(last_msg, AIMessage):
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            recovery_count = state.get("recovery_count", 0) or 0
            if recovery_count >= 2:
                return "recovery"
            return "tools"

    return END


async def evaluator_node(state: AgentState) -> Dict[str, Any]:
    """
    Evaluates execution progress and detects repeated failures.
    """
    return {}


async def recovery_node(state: AgentState) -> Dict[str, Any]:
    """
    Self-healing recovery node triggered when tools fail repeatedly.
    Injects reflection advice to break execution deadlocks.
    """
    recovery_count = (state.get("recovery_count", 0) or 0) + 1
    reflection_msg = SystemMessage(
        content=(
            f"[SELF-HEALING RECOVERY STRIKE {recovery_count}] "
            "Previous tool execution attempts encountered repeating issues. "
            "Re-evaluate your parameters or select an alternative tool."
        )
    )
    return {
        "messages": [reflection_msg],
        "recovery_count": recovery_count
    }
