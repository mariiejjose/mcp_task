import asyncio
import os
from openai import AsyncOpenAI
from mcp import Client, StdioServerParameters
from dotenv import load_dotenv
import json

load_dotenv()

MODEL = "google/gemini-2.5-flash"
MAX_TOOL_ROUNDS = 10
NEEDS_CONFIRMATION = {"create_ticket", "close_ticket"}

def to_gemini_tools(mcp_tools) -> list[dict]:
    """Convert MCP tool objects into Gemini function declarations."""
    tools = []
    for tool in mcp_tools:
        tools.append({
            "type": "function",
            "function": {
                "name":tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        })
    return tools

def as_text(result) -> str:
    """Join all text content blocks from a MCP tool result."""

    return "\n".join(block.text for block in result.content if block.type == "text")

def confirmation(tool_name: str, args: dict) -> bool:
    """Ask the user before running a tool that changes data."""
    print(f"\nGemini wants to run: {tool_name}")
    print(f"Arguments: {args}")

    answer = input("Allow this action? (y/n): ").strip().lower()
    return answer in {"y", "yes"}

async def answer(openrouter: AsyncOpenAI, mcp: Client, tools: list[dict], history: list) -> str:
    """The tool-use loop for ONE user message.
        Stop after MAX_TOOL_ROUNDS rounds. Return Gemini's final text.
        Catch errors.APIError and return a friendly message.
    """
    for _ in range(MAX_TOOL_ROUNDS):
        response = await openrouter.chat.completions.create(
            model = MODEL,
            messages = history,
            tools = tools,
        )
        message = response.choices[0].message

        if not message.tool_calls:
            history.append({
                "role": "assistant",
                "content": message.content or "",
            })

            return message.content or ""

        history.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [{
                "id": call.id,
                "type": "function",
                "function":{
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
                }for call in message.tool_calls
            ],
        })
        

        for call in message.tool_calls:
            args = json.loads(call.function.arguments)

            print(f"Calling tool: {call.function.name} "
                  f"with {call.function.arguments} ")

            if call.function.name in NEEDS_CONFIRMATION:
                confirmed = confirmation(call.function.name, args, )

                if not confirmed: 
                    history.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": ("ERROR: The user rejected this action."
                                    "The tool was NOT executed and no data was changed.")
                    })
                    continue
            result = await mcp.call_tool(call.function.name, args)

            tool_text = as_text(result)
            history.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": tool_text,
            })
    return "the tool-use limit waas reached"

async def main():
    openrouter = AsyncOpenAI(
        base_url = "https://openrouter.ai/api/v1",
        api_key = os.getenv("OPENROUTER_API_KEY"),
    )
    server = StdioServerParameters(command="python", args=["helpdesk_server.py"],)

    async with Client(server) as mcp:
        mcp_tools = (await mcp.list_tools()).tools
        tools = to_gemini_tools(mcp_tools)
        
        print("Discovered tools:")

        for tool in mcp_tools:
            print(f"-{tool.name}")

        history = [{
            "role": "system",
            "content": (
                "You are an IT helpdesk assistant."
                "Always check the FAQ before suggesting that a support ticket can be created."
                "Use the available MCP tools when needed."
                "Do not invent ticket information."
            ),
        }]
        while True:
            user_message = input("Q: ")
            history.append({
            "role": "user", 
            "content": user_message,
            })
            reply = await answer(openrouter, mcp, tools, history)

            print("A: ", reply)

if __name__ == "__main__":
    asyncio.run(main())