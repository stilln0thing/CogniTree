"""
agent.py — Main LLM agent streaming node with free Ollama + OpenAI support.
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


def get_llm_client():
    """
    Detects environment settings and returns an AsyncOpenAI client configured for
    either OpenAI Cloud or FREE local Ollama instance.
    """
    from openai import AsyncOpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        model_name = os.getenv("MODEL", "gpt-4o-mini")
        return AsyncOpenAI(api_key=api_key), model_name
    else:
        # Default to local Ollama (100% free)
        ollama_url = os.getenv("OLLAMA_HOST", "http://localhost:11434/v1")
        model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        return AsyncOpenAI(base_url=ollama_url, api_key="ollama"), model_name


async def agent_node(state: AgentState, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Main LLM processing node. Calls the language model (Ollama or OpenAI) and streams output or emits tool calls.
    """
    messages = list(state.get("messages", []))
    iteration = state.get("iteration", 0) + 1
    
    if not messages or not isinstance(messages[0], SystemMessage):
        messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))

    queue = None
    if config and "configurable" in config:
        queue = config["configurable"].get("queue")

    try:
        client, model_name = get_llm_client()

        # Convert LangChain message history into standard API message format
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

        # Call active model
        response = await client.chat.completions.create(
            model=model_name,
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
        error_text = f"Error during model invocation ({str(err)})"
        if queue:
            await queue.put(("error", error_text))
        return {
            "messages": [AIMessage(content=f"⚠️ {error_text}")],
            "iteration": iteration
        }
