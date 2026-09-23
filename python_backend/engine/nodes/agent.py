"""
agent.py — Main LLM agent streaming node with free Ollama + OpenAI tool support.
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from python_backend.engine.state import AgentState
from python_backend.tools.registry import OPENAI_TOOL_SCHEMAS

SYSTEM_PROMPT = """You are CogniTree, an enterprise-grade autonomous AI assistant.
You help users solve complex tasks using step-by-step reasoning, tool execution, and clear markdown output.
When tools are available (e.g. web_search, run_local_python_script, read_file, write_file), call them using valid tool function calls.
"""


def get_llm_client():
    """
    Detects environment settings and returns an AsyncOpenAI client configured for
    either OpenAI Cloud or FREE local Ollama instance (qwen2.5:7b).
    """
    from openai import AsyncOpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        model_name = os.getenv("MODEL", "gpt-4o-mini")
        return AsyncOpenAI(api_key=api_key), model_name
    else:
        ollama_url = os.getenv("OLLAMA_HOST", "http://localhost:11434/v1")
        model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        return AsyncOpenAI(base_url=ollama_url, api_key="ollama"), model_name


async def agent_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """
    Main LLM processing node. Calls language model with tools enabled and streams output.
    """
    messages = list(state.get("messages", []))
    iteration = state.get("iteration", 0) + 1
    
    if not messages or not isinstance(messages[0], SystemMessage):
        messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))

    queue = None
    if config:
        configurable = getattr(config, "configurable", None) or (config.get("configurable") if isinstance(config, dict) else None)
        if configurable and isinstance(configurable, dict):
            queue = configurable.get("queue")

    can_enqueue = queue is not None and hasattr(queue, "put") and callable(queue.put)

    try:
        client, model_name = get_llm_client()

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

        # Call model with tool schemas passed!
        response = await client.chat.completions.create(
            model=model_name,
            messages=oai_messages,
            tools=OPENAI_TOOL_SCHEMAS,
            tool_choice="auto"
        )

        resp_msg = response.choices[0].message
        ai_content = resp_msg.content or ""
        tool_calls = []

        if resp_msg.tool_calls:
            for tc in resp_msg.tool_calls:
                try:
                    parsed_args = json.loads(tc.function.arguments)
                except Exception:
                    parsed_args = {}
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": parsed_args
                })

        if can_enqueue and ai_content:
            await queue.put(("token", ai_content))

        return {
            "messages": [AIMessage(content=ai_content, tool_calls=tool_calls)],
            "iteration": iteration
        }

    except Exception as err:
        error_text = f"Error during model invocation ({str(err)})"
        if can_enqueue:
            await queue.put(("error", error_text))
        return {
            "messages": [AIMessage(content=f"⚠️ {error_text}")],
            "iteration": iteration
        }
