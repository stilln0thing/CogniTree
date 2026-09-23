"""
tools.py — Dynamic tool execution node.
"""

import json
from typing import Dict, Any, List, Optional
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from python_backend.engine.state import AgentState
from python_backend.tools.registry import execute_tool_by_name


async def tools_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """
    Executes requested tool calls dynamically using registered tools.
    """
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_msg = messages[-1]
    if not isinstance(last_msg, AIMessage) or not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
        return {}

    queue = None
    if config:
        configurable = getattr(config, "configurable", None) or (config.get("configurable") if isinstance(config, dict) else None)
        if configurable and isinstance(configurable, dict):
            queue = configurable.get("queue")

    can_enqueue = queue is not None and hasattr(queue, "put") and callable(queue.put)

    tool_results = []
    for tool_call in last_msg.tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        call_id = tool_call.get("id", "call_default")

        if can_enqueue:
            await queue.put(("tool_start", {"name": tool_name, "args": tool_args}))

        # Dispatch real tool execution!
        result_output = execute_tool_by_name(tool_name, tool_args)

        if can_enqueue:
            await queue.put(("tool_done", {"name": tool_name, "result": result_output}))

        tool_results.append(
            ToolMessage(
                content=result_output,
                name=tool_name,
                tool_call_id=call_id
            )
        )

    return {"messages": tool_results}
