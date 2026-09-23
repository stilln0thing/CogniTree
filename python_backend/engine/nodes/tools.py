"""
tools.py — Dynamic tool execution node.
"""

import json
from typing import Dict, Any, List
from langchain_core.messages import AIMessage, ToolMessage
from python_backend.engine.state import AgentState


async def tools_node(state: AgentState, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Executes requested tool calls concurrently or sequentially.
    """
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_msg = messages[-1]
    if not isinstance(last_msg, AIMessage) or not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
        return {}

    queue = None
    if config and "configurable" in config:
        queue = config["configurable"].get("queue")

    tool_results = []
    for tool_call in last_msg.tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        call_id = tool_call.get("id", "call_default")

        if queue:
            await queue.put(("tool_start", {"name": tool_name, "args": tool_args}))

        # Mock tool execution output for base node testing
        result_output = f"Tool '{tool_name}' executed successfully with args: {json.dumps(tool_args)}"

        if queue:
            await queue.put(("tool_done", {"name": tool_name, "result": result_output}))

        tool_results.append(
            ToolMessage(
                content=result_output,
                name=tool_name,
                tool_call_id=call_id
            )
        )

    return {"messages": tool_results}
