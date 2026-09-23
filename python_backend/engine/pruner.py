"""
pruner.py — Context Pruning, Tombstoning, and SHA-256 Block Summarization.
"""

import hashlib
import re
from typing import List, Dict, Any, Tuple
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, SystemMessage


# In-memory summary cache keyed by SHA-256 hash of turn block contents
_SUMMARY_CACHE: Dict[str, str] = {}


def tombstone_failed_retries(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    Replaces verbose error logs and stack traces from resolved tool attempts with 1-line tombstones.
    If a tool call failed but was followed by a successful retry of the same tool, tombstone the failure.
    """
    if len(messages) < 3:
        return messages

    pruned_messages = list(messages)
    
    for i in range(len(pruned_messages) - 1):
        msg = pruned_messages[i]
        next_msg = pruned_messages[i + 1]

        # Check if current message is a failed ToolMessage
        if isinstance(msg, ToolMessage) and ("error" in msg.content.lower() or "exception" in msg.content.lower()):
            # If the next message is a successful ToolMessage for the same tool, tombstone the current error
            if isinstance(next_msg, ToolMessage) and next_msg.name == msg.name and "error" not in next_msg.content.lower():
                tombstone_content = f"[TOMBSTONE: Resolved error trace for tool '{msg.name}']"
                pruned_messages[i] = ToolMessage(
                    content=tombstone_content,
                    name=msg.name,
                    tool_call_id=msg.tool_call_id
                )

    return pruned_messages


def truncate_bulky_output(text: str, max_chars: int = 2000) -> str:
    """
    Truncates massive tool outputs (>max_chars) keeping head and tail snippets.
    """
    if not isinstance(text, str) or len(text) <= max_chars:
        return text

    head_length = max_chars // 2
    tail_length = max_chars // 2
    omitted_count = len(text) - (head_length + tail_length)

    head = text[:head_length]
    tail = text[-tail_length:]

    return f"{head}\n\n... [TRUNCATED {omitted_count} characters for context optimization] ...\n\n{tail}"


def compute_block_sha256(messages: List[BaseMessage]) -> str:
    """
    Computes a deterministic SHA-256 hash of a list of messages.
    """
    raw_text = "".join([f"{msg.type}:{msg.content}" for msg in messages])
    return hashlib.sha256(raw_text.encode("utf-8")).hexdigest()


def prune_context(messages: List[BaseMessage], max_tokens_approx: int = 4000) -> List[BaseMessage]:
    """
    Main context optimization pipeline:
    1. Tombstones resolved tool errors.
    2. Truncates bulky tool outputs.
    """
    # Step 1: Tombstone resolved tool errors
    cleaned_messages = tombstone_failed_retries(messages)

    # Step 2: Truncate bulky outputs
    processed_messages = []
    for msg in cleaned_messages:
        if isinstance(msg, ToolMessage):
            truncated_content = truncate_bulky_output(msg.content)
            processed_messages.append(
                ToolMessage(
                    content=truncated_content,
                    name=msg.name,
                    tool_call_id=msg.tool_call_id
                )
            )
        else:
            processed_messages.append(msg)

    return processed_messages
