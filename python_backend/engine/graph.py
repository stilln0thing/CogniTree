"""
graph.py — Multi-node LangGraph compilation and execution streaming.
"""

import asyncio
from typing import Any, Optional, Dict, List
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END

from python_backend.engine.state import AgentState
from python_backend.engine.nodes.planner import planner_node
from python_backend.engine.nodes.agent import agent_node
from python_backend.engine.nodes.tools import tools_node
from python_backend.engine.nodes.evaluator import should_continue, recovery_node, evaluator_node


def build_graph(checkpointer: Optional[Any] = None) -> Any:
    """
    Constructs and compiles the multi-node StateGraph:
    planner -> agent -> should_continue -> (tools -> agent | recovery -> agent | END)
    Attaches checkpointer for stateful time-travel checkpoints if provided.
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("evaluator", evaluator_node)
    workflow.add_node("recovery", recovery_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "recovery": "recovery",
            END: END
        }
    )
    workflow.add_edge("tools", "agent")
    workflow.add_edge("recovery", "agent")

    return workflow.compile(checkpointer=checkpointer)


compiled_graph = build_graph()


def set_compiled_graph(graph: Any) -> None:
    """Updates active compiled graph instance."""
    global compiled_graph
    compiled_graph = graph


def get_compiled_graph() -> Any:
    """Returns active compiled graph instance."""
    return compiled_graph


async def stream_graph_execution(
    delta_state: Dict[str, Any],
    queue: asyncio.Queue,
    thread_id: Optional[str] = None,
    checkpoint_id: Optional[str] = None
) -> List[BaseMessage]:
    """
    Executes the multi-node graph with stateful checkpoints:
    - Passes delta_state (new turn messages only)
    - Points configurable['checkpoint_id'] to checkpoint_id when branching
    - Pushes events to queue ('token', 'tool_start', 'tool_done', 'done', 'error')
    """
    configurable: Dict[str, Any] = {"queue": queue}
    if thread_id:
        configurable["thread_id"] = thread_id
    if checkpoint_id and checkpoint_id != "node_root":
        configurable["checkpoint_id"] = checkpoint_id

    config: Dict[str, Any] = {"configurable": configurable}

    try:
        graph = get_compiled_graph()
        final_state = await graph.ainvoke(delta_state, config=config)
        messages = final_state.get("messages", [])
        await queue.put(("done", messages))
        return messages
    except Exception as exc:
        await queue.put(("error", str(exc)))
        return delta_state.get("messages", [])
    finally:
        await queue.put(("__end__", None))
