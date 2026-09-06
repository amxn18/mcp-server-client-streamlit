import asyncio
import json

import streamlit as st

from dotenv import load_dotenv

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from langchain_huggingface import (
    ChatHuggingFace,
    HuggingFaceEndpoint,
)

from langchain_mcp_adapters.client import MultiServerMCPClient


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


SYSTEM_PROMPT = (
    "You are a helpful assistant with access to MCP tools. "
    "Use the available tools whenever they are appropriate. "
    "Do not narrate tool execution or status updates. "
    "After the tools finish, provide only the concise final answer."
)


st.set_page_config(
    page_title="MCP Expense Assistant",
    page_icon="💰",
    layout="centered",
)


st.title("💰 MCP Expense Assistant")
st.caption("Powered by LangChain + MCP + FastMCP + PostgreSQL")


async def process_message(user_text):

    client = MultiServerMCPClient(SERVERS)

    tools = await client.get_tools()

    tool_by_name = {
        tool.name: tool
        for tool in tools
    }

    llm = HuggingFaceEndpoint(
        repo_id="Qwen/Qwen3-4B-Instruct-2507",
        task="text-generation",
    )

    model = ChatHuggingFace(llm=llm)

    model_with_tools = model.bind_tools(tools)

    first_response = await model_with_tools.ainvoke(
        st.session_state.history
    )

    tool_calls = getattr(
        first_response,
        "tool_calls",
        None,
    )

    if not tool_calls:
        return first_response

    st.session_state.history.append(
        first_response
    )

    tool_messages = []

    for tool_call in tool_calls:

        tool_name = tool_call["name"]

        tool_args = (
            tool_call.get("args")
            or {}
        )

        tool_call_id = tool_call["id"]

        if isinstance(tool_args, str):

            try:
                tool_args = json.loads(
                    tool_args
                )

            except Exception:
                pass

        selected_tool = tool_by_name[
            tool_name
        ]

        result = await selected_tool.ainvoke(
            tool_args
        )

        tool_messages.append(
            ToolMessage(
                tool_call_id=tool_call_id,
                content=json.dumps(result),
            )
        )

    st.session_state.history.extend(
        tool_messages
    )

    final_response = await model.ainvoke(
        st.session_state.history
    )

    return final_response


if "history" not in st.session_state:

    st.session_state.history = [
        SystemMessage(
            content=SYSTEM_PROMPT
        )
    ]


with st.sidebar:

    st.header("⚙️ MCP Setup")

    st.success(
        "Math MCP Server"
    )

    st.success(
        "Expense MCP Server"
    )

    st.divider()

    st.subheader(
        "Available MCP Servers"
    )

    st.write("🔢 Math")
    st.write("💰 Expense")

    st.divider()

    if st.button("🗑️ Clear Chat"):

        st.session_state.history = [
            SystemMessage(
                content=SYSTEM_PROMPT
            )
        ]

        st.rerun()


for msg in st.session_state.history:

    if isinstance(
        msg,
        HumanMessage
    ):

        with st.chat_message("user"):

            st.markdown(
                msg.content
            )

    elif isinstance(
        msg,
        AIMessage
    ):

        if getattr(
            msg,
            "tool_calls",
            None,
        ):
            continue

        with st.chat_message(
            "assistant"
        ):

            st.markdown(
                msg.content or ""
            )


user_text = st.chat_input(
    "Ask something..."
)


if user_text:

    with st.chat_message("user"):

        st.markdown(
            user_text
        )

    st.session_state.history.append(
        HumanMessage(
            content=user_text
        )
    )

    final_response = asyncio.run(
        process_message(
            user_text
        )
    )

    with st.chat_message(
        "assistant"
    ):

        st.markdown(
            final_response.content or ""
        )

    st.session_state.history.append(
        AIMessage(
            content=final_response.content or ""
        )
    )