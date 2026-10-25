"""
agent.py — Main LLM agent streaming node with free Ollama + OpenAI tool support.
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from python_backend.logger import setup_logger
from python_backend.engine.state import AgentState
from python_backend.engine.pruner import prune_context
from python_backend.tools.registry import OPENAI_TOOL_SCHEMAS
from python_backend.server.dependencies import record_token_usage

logger = setup_logger("cognitree.engine.nodes.agent")

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
        logger.info("Configured AsyncOpenAI client using OpenAI Cloud API key for model '%s'", model_name)
        return AsyncOpenAI(api_key=api_key), model_name
    else:
        ollama_url = os.getenv("OLLAMA_HOST", "http://localhost:11434/v1")
        model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        logger.info("Configured AsyncOpenAI client using local Ollama endpoint '%s' for model '%s'", ollama_url, model_name)
        return AsyncOpenAI(base_url=ollama_url, api_key="ollama"), model_name


async def agent_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """
    Main LLM processing node. Calls language model with tools enabled and streams output.
    """
    messages = list(state.get("messages", []))
    iteration = state.get("iteration", 0) + 1
    logger.info("Executing agent_node turn (iteration=%d, message_history_length=%d)", iteration, len(messages))
    
    if not messages or not isinstance(messages[0], SystemMessage):
        messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))

    # removed nosiy failed tool outputs from context before model call
    messages = prune_context(messages)

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

        logger.info("Invoking model '%s' with %d messages and %d registered tool schemas (streaming=True).", model_name, len(oai_messages), len(OPENAI_TOOL_SCHEMAS))

        # ── True token-by-token streaming ─────────────────────────────────────
        stream = await client.chat.completions.create(
            model=model_name,
            messages=oai_messages,
            tools=OPENAI_TOOL_SCHEMAS,
            tool_choice="auto",
            stream=True,
            stream_options={"include_usage": True},  # Token usage arrives in final chunk
        )

        ai_content = ""
        # Accumulate tool call argument fragments streamed across multiple chunks
        # Structure: { chunk_index: {"id": str, "name": str, "args_buf": str} }
        tool_call_accum: Dict[int, Dict[str, Any]] = {}
        prompt_tokens = 0
        completion_tokens = 0

        async for chunk in stream:
            # ── Token usage (only populated in the final sentinel chunk) ──────
            if hasattr(chunk, "usage") and chunk.usage:
                prompt_tokens = getattr(chunk.usage, "prompt_tokens", 0) or 0
                completion_tokens = getattr(chunk.usage, "completion_tokens", 0) or 0

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # ── Stream text content tokens to queue immediately ───────────────
            if delta.content:
                ai_content += delta.content
                if can_enqueue:
                    await queue.put(("token", delta.content))

            # ── Accumulate streamed tool call argument fragments ───────────────
            if delta.tool_calls:
                for tc_chunk in delta.tool_calls:
                    idx = tc_chunk.index
                    if idx not in tool_call_accum:
                        tool_call_accum[idx] = {"id": "", "name": "", "args_buf": ""}
                    if tc_chunk.id:
                        tool_call_accum[idx]["id"] = tc_chunk.id
                    if tc_chunk.function and tc_chunk.function.name:
                        tool_call_accum[idx]["name"] = tc_chunk.function.name
                    if tc_chunk.function and tc_chunk.function.arguments:
                        tool_call_accum[idx]["args_buf"] += tc_chunk.function.arguments

        # ── Record token usage telemetry ──────────────────────────────────────
        if prompt_tokens > 0 or completion_tokens > 0:
            record_token_usage(prompt_tokens, completion_tokens)
            logger.info("Recorded token usage: prompt=%d, completion=%d", prompt_tokens, completion_tokens)
        else:
            logger.info("Model response did not include token usage; telemetry was not updated.")

        # ── Reconstruct full tool_calls from accumulated stream fragments ──────
        tool_calls = []
        for idx in sorted(tool_call_accum.keys()):
            entry = tool_call_accum[idx]
            try:
                parsed_args = json.loads(entry["args_buf"]) if entry["args_buf"] else {}
            except Exception:
                parsed_args = {}
            tool_calls.append({"id": entry["id"], "name": entry["name"], "args": parsed_args})

        if tool_calls:
            logger.info("Model requested tool execution for tools: %s", [tc["name"] for tc in tool_calls])

        logger.info("agent_node completed successfully (streaming). Response length: %d chars.", len(ai_content))
        return {
            "messages": [AIMessage(content=ai_content, tool_calls=tool_calls)],
            "iteration": iteration
        }

    except Exception as err:
        logger.error("Error encountered in agent_node during model invocation: %s", str(err), exc_info=True)
        error_text = f"Error during model invocation ({str(err)})"
        if can_enqueue:
            await queue.put(("error", error_text))
        return {
            "messages": [AIMessage(content=f"{error_text}")],
            "iteration": iteration
        }
