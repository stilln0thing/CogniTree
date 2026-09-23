"""
02_graph_demo.py — Phase 2: LangGraph Engine Verification Demo

Demonstrates multi-node state graph compilation, execution, and event streaming.
"""

import asyncio
import sys
import os

# Add project root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_core.messages import HumanMessage
from python_backend.engine.graph import stream_graph_execution


async def main():
    print("🌿 Testing CogniTree LangGraph Multi-Node Engine...\n")

    user_prompt = "Find recent AI agent papers and write a 2-bullet summary."
    print(f"👤 User Input: '{user_prompt}'\n")

    queue = asyncio.Queue()
    delta_state = {"messages": [HumanMessage(content=user_prompt)]}

    # Start graph execution in background task
    task = asyncio.create_task(
        stream_graph_execution(
            delta_state=delta_state,
            queue=queue,
            thread_id="test_thread_001"
        )
    )

    # Listen to event queue
    while True:
        event_type, payload = await queue.get()
        if event_type == "__end__":
            break
        elif event_type == "token":
            print(f"[STREAM TOKEN]: {payload}")
        elif event_type == "tool_start":
            print(f"[TOOL START]: {payload}")
        elif event_type == "tool_done":
            print(f"[TOOL DONE]: {payload}")
        elif event_type == "done":
            print("\n✅ Graph execution completed successfully!")

    await task

if __name__ == "__main__":
    asyncio.run(main())
