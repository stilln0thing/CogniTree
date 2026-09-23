"""
01_tool_calling.py — Phase 1: Basic LLM Function / Tool Calling Demo with Ollama Support

Demonstrates how Large Language Models (LLMs) interact with Python code using Tool Calling.
Supports FREE local execution via Ollama (e.g. llama3.2) or OpenAI.
"""

import asyncio
import json
import os
from typing import Any, Dict
from openai import AsyncOpenAI


# ── Step 1: Define Python Tool Function & JSON Schema ─────────────────────────

def calculate_mortgage(principal: float, rate_annual: float, years: int) -> Dict[str, Any]:
    """Calculates monthly payment for a fixed-rate mortgage."""
    r = (rate_annual / 100) / 12
    n = years * 12
    if r == 0:
        monthly = principal / n
    else:
        monthly = principal * (r * (1 + r)**n) / ((1 + r)**n - 1)
    
    total_paid = monthly * n
    total_interest = total_paid - principal
    
    return {
        "monthly_payment": round(monthly, 2),
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2)
    }


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_mortgage",
            "description": "Calculates monthly payment and total interest for a fixed-rate loan/mortgage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "principal": {
                        "type": "number",
                        "description": "The loan principal amount in USD (e.g. 400000)."
                    },
                    "rate_annual": {
                        "type": "number",
                        "description": "The annual interest rate as a percentage (e.g. 6.5)."
                    },
                    "years": {
                        "type": "integer",
                        "description": "The loan term in years (e.g. 30)."
                    }
                },
                "required": ["principal", "rate_annual", "years"]
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Executes the local tool function matching tool_name and returns JSON string."""
    if tool_name == "calculate_mortgage":
        result = calculate_mortgage(**arguments)
        return json.dumps(result)
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


# ── Step 2: Configure Client (Ollama vs OpenAI) ───────────────────────────────

def get_async_client() -> tuple[AsyncOpenAI, str]:
    """
    Returns an AsyncOpenAI client configured for either local Ollama (100% free)
    or OpenAI API based on environment variables.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("🌐 Using OpenAI Cloud API Key")
        return AsyncOpenAI(api_key=api_key), os.getenv("MODEL", "gpt-4o-mini")
    else:
        print("🦙 Using Local FREE Ollama Model (http://localhost:11434/v1)")
        ollama_url = os.getenv("OLLAMA_HOST", "http://localhost:11434/v1")
        model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
        return AsyncOpenAI(base_url=ollama_url, api_key="ollama"), model_name


# ── Step 3: Tool Calling Execution Loop ───────────────────────────────────────

async def run_demo():
    user_prompt = "What would be my monthly payment for a $400,000 house loan at 6.5% interest over 30 years?"
    print(f"👤 User Query: {user_prompt}\n")

    client, model_name = get_async_client()
    print(f"🤖 Active Model: '{model_name}'\n")

    messages = [{"role": "user", "content": user_prompt}]

    try:
        # Step A: Send user prompt + tool schema to LLM
        print("📡 Sending prompt and tool schema to LLM...")
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        # Step B: Check if LLM requested a tool call
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)

            print(f"🛠️ LLM selected tool: '{func_name}'")
            print(f"📋 Extracted arguments: {json.dumps(func_args)}")

            # Step C: Execute tool locally
            tool_output_str = execute_tool(func_name, func_args)
            print(f"✅ Tool result output: {tool_output_str}\n")

            # Step D: Append tool call and output to message history
            messages.append(response_message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": func_name,
                "content": tool_output_str
            })

            # Step E: Return tool result back to LLM for final synthesis
            print("📡 Sending tool results back to LLM for final answer...")
            final_response = await client.chat.completions.create(
                model=model_name,
                messages=messages
            )
            print(f"\n💬 Final LLM Output:\n{final_response.choices[0].message.content}")

        else:
            print(f"\n💬 Direct Response (No tool called):\n{response_message.content}")

    except Exception as err:
        print(f"❌ Execution Exception: {err}")
        print("\nFallback simulation:")
        simulated_args = {"principal": 400000, "rate_annual": 6.5, "years": 30}
        tool_res = execute_tool("calculate_mortgage", simulated_args)
        print(f"Executed result: {tool_res}")


if __name__ == "__main__":
    asyncio.run(run_demo())
