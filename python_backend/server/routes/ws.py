"""
ws.py — Real-time WebSocket streaming route for CogniTree client UI.
"""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage
from python_backend.engine.graph import stream_graph_execution

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint supporting real-time prompt receiving, LLM token streaming,
    tool execution status updates, and decision tree state checkpointing.
    """
    await websocket.accept()
    print("Client connected to WebSocket /ws")

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            msg_type = payload.get("type", "chat")
            prompt = payload.get("prompt", "")
            thread_id = payload.get("thread_id", "default_thread")
            checkpoint_id = payload.get("checkpoint_id", None)

            if msg_type == "chat" and prompt:
                queue = asyncio.Queue()
                delta_state = {"messages": [HumanMessage(content=prompt)]}

                # Launch graph execution task
                execution_task = asyncio.create_task(
                    stream_graph_execution(
                        delta_state=delta_state,
                        queue=queue,
                        thread_id=thread_id,
                        checkpoint_id=checkpoint_id
                    )
                )

                # Stream events back over WebSocket
                while True:
                    event_type, event_payload = await queue.get()
                    if event_type == "__end__":
                        break
                    
                    response_event = {"type": event_type, "payload": event_payload}
                    if event_type == "token":
                        response_event = {"type": "token", "content": event_payload}
                    elif event_type == "done":
                        response_event = {"type": "done", "status": "complete"}

                    await websocket.send_text(json.dumps(response_event, default=str))

                await execution_task

    except WebSocketDisconnect:
        print("Client disconnected from WebSocket /ws")
    except Exception as exc:
        print(f"WebSocket Exception: {str(exc)}")
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(exc)}))
        except Exception:
            pass
