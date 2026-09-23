"""
planner.py — Task decomposition planner node.
"""

from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from python_backend.engine.state import AgentState


PLANNER_SYSTEM_PROMPT = """You are an expert AI execution planner.
Given a user query, analyze if it requires multi-step tool execution.
If so, break down the execution into 2-4 concise, ordered steps.
If the query is a simple question or chat, return an empty plan.
Format your output as a numbered list of steps or simple bullets.
"""


async def planner_node(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes the latest user message and initializes execution plan if needed.
    """
    messages = state.get("messages", [])
    if not messages:
        return {"plan": []}

    latest_message = messages[-1]
    if not isinstance(latest_message, HumanMessage):
        return {}

    user_text = latest_message.content
    
    # For short simple prompts, skip planning overhead
    if len(user_text.split()) < 8 and not any(kw in user_text.lower() for kw in ["search", "write", "run", "calculate", "find", "create"]):
        return {"plan": [], "iteration": 0}

    # Formulate a simple plan decomposition
    plan_steps = [
        f"1. Understand and analyze request: '{user_text[:60]}...'",
        "2. Execute relevant tools if required.",
        "3. Synthesize findings into clear final output."
    ]

    return {
        "plan": plan_steps,
        "iteration": 0,
        "recovery_count": 0
    }
