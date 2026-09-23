"""
01_tool_calling.py — Phase 1: Basic LLM Function / Tool Calling Demo

This standalone script demonstrates how Large Language Models (LLMs) interact
with Python code using Tool Calling (Function Calling).

Flow:
1. Define a tool function and its JSON schema.
2. Send user prompt + tool schema to the model.
3. Model inspects prompt and returns a tool call request (function name + parameters).
4. Local code executes the tool and returns the tool output back to the model.
5. Model uses tool output to produce the final human-readable answer.
"""

import asyncio
import json
import os
from typing import Any, Dict


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


# JSON Schema passed to the LLM so it knows tool parameters and types
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
                        "description": "The loan principal amount in USD (e.g. 300000)."
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


# ── Step 2: Tool Dispatcher ───────────────────────────────────────────────────

def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Executes the local tool function matching tool_name and returns JSON string."""
    if tool_name == "calculate_mortgage":
        result = calculate_mortgage(**arguments)
        return json.dumps(result)
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


# ── Step 3: Main Async Function Calling Loop ──────────────────────────────────

async def run_demo():
    user_prompt = "What would be my monthly payment for a $400,000 house loan at 6.5% interest over 30 years?"
    print(f"👤 User: {user_prompt}\n")

    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)

        # First Call: Send Prompt + Available Tools to LLM
        messages = [{"role": "user", "content": user_prompt}]
        print("🤖 Invoking LLM with tool schemas...")
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        # Check if model requested a tool call
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)

            print(f"🛠️ LLM selected tool: '{func_name}'")
            print(f"📋 Arguments extracted by LLM: {json.dumps(func_args, indent=2)}")

            # Execute tool locally
            tool_output_str = execute_tool(func_name, func_args)
            print(f"✅ Tool execution result: {tool_output_str}\n")

            # Append assistant's call and tool's response to message history
            messages.append(response_message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": func_name,
                "content": tool_output_str
            })

            # Second Call: Send tool output back to LLM to generate final response
            print("🤖 Sending tool result back to LLM for final response...")
            final_response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            print(f"💬 Final Assistant Output:\n{final_response.choices[0].message.content}")
        else:
            print(f"💬 Assistant Direct Response:\n{response_message.content}")

    else:
        # Offline/Simulated Demonstration Mode
        print("⚠️ OPENAI_API_KEY not found in environment. Running simulated demonstration:")
        simulated_args = {"principal": 400000, "rate_annual": 6.5, "years": 30}
        print(f"🛠️ Simulated Tool Choice: calculate_mortgage({simulated_args})")
        tool_res = execute_tool("calculate_mortgage", simulated_args)
        print(f"✅ Executed Tool Result: {tool_res}")
        res_data = json.loads(tool_res)
        print(
            f"\n💬 Simulated Assistant Output:\n"
            f"For a $400,000 loan at 6.5% interest over 30 years, "
            f"your monthly payment will be **${res_data['monthly_payment']}**. "
            f"Total paid over 30 years will be ${res_data['total_paid']:,} "
            f"(with ${res_data['total_interest']:,} in interest)."
        )


if __name__ == "__main__":
    asyncio.run(run_demo())
