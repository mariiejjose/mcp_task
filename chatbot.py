import asyncio
import os
from google import genai
from google.genai import errors, types
from mcp import Client, StdioServerParameters

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_TOOL_ROUNDS = 10
NEEDS_CONFIRMATION = {"create_ticket", "close_ticket"}

def to_gemini_tools(mcp_tools) -> list[types.Tool]:
    """Convert MCP tool objects into Gemini function declarations."""
    return [types.Tool(function_declarations=[types.FunctionDeclaration(
        name = tool.name,
        description = tool.description or "",
        parameters_json_schema = tool.input_schema,
    ) for tool in mcp_tools
    ])]

async def main():
    server = StdioServerParameters(command="python", args=["helpdesk_server.py"],)

    async with Client(server) as mcp:
        mcp_tools = (await mcp.list_tools()).tools
        tools = to_gemini_tools(mcp_tools)

        print("Discovered tools:")

        for tool in mcp_tools:
            print(f"- {tool.name}")

if __name__ == "__main__":
    asyncio.run(main())