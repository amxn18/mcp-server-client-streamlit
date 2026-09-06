import asyncio
import json

from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

load_dotenv()


SERVERS = {
    "math": {
        "transport": "stdio",
        "command": r"C:\Users\Dell\AppData\Local\Programs\Python\Python311\Scripts\uv.exe",
        "args": [
            "run",
            "--directory",
            r"C:\Users\Dell\OneDrive\Desktop\mcp-client-server\mcp-server",
            "fastmcp",
            "run",
            "arithmetic-roll-dice-server.py",
        ],
    },
    "expense": {
        "transport": "stdio",
        "command": r"C:\Users\Dell\AppData\Local\Programs\Python\Python311\Scripts\uv.exe",
        "args": [
            "run",
            "--directory",
            r"C:\Users\Dell\OneDrive\Desktop\mcp-client-server\mcp-server",
            "fastmcp",
            "run",
            "expense-tracker-server.py",
        ],
    },
}


llm = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen3-4B-Instruct-2507",
    task="text-generation",
)


async def main():

    # Connect to both MCP servers
    client = MultiServerMCPClient(SERVERS)

    # Get all tools exposed by both MCP servers
    tools = await client.get_tools()

    # Store tools by name
    named_tools = {}

    for tool in tools:
        named_tools[tool.name] = tool

    # Create LLM
    model = ChatHuggingFace(llm=llm)

    # Bind MCP tools to the LLM
    toolsLLM = model.bind_tools(tools)

    # User prompt
    prompt1 = "Product of 12 and 15 using the provided math tool"

    # Ask LLM which tool it should use
    response = await toolsLLM.ainvoke(prompt1)

    # If LLM doesn't want to use a tool
    if not getattr(response, "tool_calls", None):
        print("LLM Reply:", response.content)
        return

    # Execute the requested MCP tools
    tool_messages = []

    for tc in response.tool_calls:

        selected_tool = tc["name"]
        selected_tool_args = tc.get("args") or {}
        selected_tool_id = tc["id"]

        result = await named_tools[selected_tool].ainvoke(
            selected_tool_args
        )

        tool_messages.append(
            ToolMessage(
                tool_call_id=selected_tool_id,
                content=json.dumps(result),
            )
        )

    # Send the tool result back to the LLM
    finalResponse = await model.ainvoke(
        [prompt1, response, *tool_messages]
    )

    print(f"Final response: {finalResponse.content}")


if __name__ == "__main__":
    asyncio.run(main())