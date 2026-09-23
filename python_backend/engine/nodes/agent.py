"""
agent.py — Main LLM agent streaming node.
"""

import os
import json
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage
from python_backend.engine.state import AgentState

SYSTEM_PROMPT = """You are CogniTree, an enterprise-grade autonomous AI assistant.
You help users solve complex tasks using step-by-step reasoning, tool execution, and clear markdown output.
When tools are available, call them accurately with valid arguments.
"""


async def agent_node(state: AgentState, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Main LLM processing node. Calls the language model and streams output or emits tool calls.
    """
    messages = list(state.get("messages", []))
    iteration = state.get("iteration", 0) + 1
    
    # Check if system message is present, add default if missing
    if not messages or not isinstance(messages[0], SystemMessage):
        messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))

    api_key = os.getenv("OPENAI_API_KEY")
    queue = None
    if config and "configurable" in config:
        queue = config["configurable"].get("queue")

    if api_key:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            
            # Convert langchain messages to OpenAI message format
            oai_messages = []
            for msg in messages:
                if isinstance(msg, SystemMessage):
                    oai_messages.append({"role": "system", "content": msg.content})
                elif isinstance(msg, HumanMessage):
                    oai_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    item = {"role": "assistant", "content": msg.content or ""}
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        item["tool_calls"] = [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {"name": tc["name"], "arguments": json.dumps(tc["args"])}
                            }
                            for tc in msg.tool_calls
                        ]
                    oai_messages.append(item)
                elif isinstance(msg, ToolMessage):
                    oai_messages.append({
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id,
                        "content": msg.content
                    })

            # Call OpenAI model
            response = await client.chat.completions.create(
                model=os.getenv("MODEL", "gpt-4o-mini"),
                messages=oai_messages
            )
            
            resp_msg = response.choices[0].message
            ai_content = resp_msg.content or ""
            
            if queue and ai_content:
                await queue.put(("token", ai_content))
                
            return {
                "messages": [AIMessage(content=ai_content)],
                "iteration": iteration
            }
        except Exception as err:
            error_text = f"Error during model invocation: {str(err)}"
            if queue:
                await queue.put(("error", error_text))
            return {
                "messages": [AIMessage(content=f"⚠️ {error_text}")],
                "iteration": iteration
            }

    # Offline / Mock Fallback Mode
    last_msg = messages[-1] if messages else HumanMessage(content="")
    content = f"CogniTree processed query: '{last_msg.content}'. (Running in offline mode)."
    if queue:
        await queue.put(("token", content))
        
    return {
        "messages": [AIMessage(content=content)],
        "iteration": iteration
    }
