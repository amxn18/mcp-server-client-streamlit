# MCP Expense Tracker Streamlit Client

A Streamlit-based AI expense assistant that connects to multiple local MCP servers using the Model Context Protocol (MCP).

The application uses LangChain and Qwen to understand natural-language requests and automatically call the appropriate MCP tools. The expense-related tools interact with PostgreSQL, while the arithmetic tools are provided by a separate local MCP server.

## Architecture

```text
                         ┌──────────────────────┐
                         │    Streamlit App     │
                         │      mcp-client      │
                         └──────────┬───────────┘
                                    │
                                    │ LangChain
                                    │ + Qwen
                                    ▼
                         ┌──────────────────────┐
                         │ MultiServerMCPClient │
                         └──────────┬───────────┘
                                    │
                   ┌────────────────┴────────────────┐
                   │                                 │
                 stdio                             stdio
                   │                                 │
                   ▼                                 ▼
        ┌──────────────────────┐          ┌──────────────────────┐
        │   Math MCP Server    │          │ Expense MCP Server   │
        │                      │          │                      │
        │ • add                │          │ • add_expense        │
        │ • subtract           │          │ • list_expenses      │
        │ • multiply           │          │ • summarize_expenses │
        │ • divide             │          │ • edit_expense       │
        │ • rollDice           │          │ • delete_expense     │
        │                      │          │ • credit             │
        └──────────────────────┘          └──────────┬───────────┘
                                                      │
                                                      ▼
                                             ┌──────────────────┐
                                             │   PostgreSQL     │
                                             │ expense-tracker  │
                                             └──────────────────┘
```

## Features

- Natural-language expense management
- Add expenses
- List expenses by date range
- Summarize expenses
- Edit existing expenses
- Delete expenses
- Add credits such as salary or income
- Arithmetic operations through a separate MCP server
- Dice rolling through the math MCP server
- Multiple MCP servers connected through `MultiServerMCPClient`
- Qwen LLM integration through Hugging Face
- Streamlit chat interface
- Persistent conversation history during the Streamlit session
- Clear chat functionality
- PostgreSQL-backed expense storage
- Local MCP servers communicating through stdio

## MCP Servers

The client connects to two local MCP servers.

### Math MCP Server

The math server provides:

- `add`
- `subtract`
- `multiply`
- `divide`
- `rollDice`

### Example Requests

```text
What is 25 + 75?

Calculate 500 / 25.

Multiply 12 by 8.

Roll 3 dice.
```

### Expense MCP Server

The expense server provides:

- `add_expense`
- `list_expenses`
- `summarize_expenses`
- `edit_expense`
- `delete_expense`
- `credit`

### Example Requests

```text
Add an expense of Rs 500 for groceries.

Show my expenses from September 1 to September 5.

Summarize my expenses.

Edit expense 5 and change the amount to Rs 750.

Delete expense 8.

Add my salary of Rs 50000 as a credit.
```

## Technology Stack

- Python
- Streamlit
- LangChain
- LangChain Hugging Face
- LangChain MCP Adapters
- FastMCP
- PostgreSQL
- Hugging Face Inference API
- Qwen
- python-dotenv
- uv

## Project Structure

### Client

```text
mcp-client/
│
├── client2.py
├── .env
├── .gitignore
├── pyproject.toml
├── README.md
└── uv.lock
```

### Complete Project Structure

The MCP servers are located in the separate `mcp-server` project.

```text
mcp-client-server/
│
├── mcp-client/
│
└── mcp-server/
    │
    ├── arithmetic-roll-dice-server.py
    ├── expense-tracker-server.py
    │
    └── db/
        ├── connection.py
        └── __init__.py
```

## Prerequisites

Make sure the following are installed:

- Python 3.11+
- uv
- PostgreSQL
- Streamlit
- A Hugging Face account
- A Hugging Face API token

The MCP server project must also be available locally because the client starts both MCP servers through stdio.

## Environment Variables

Create a `.env` file inside the `mcp-client` directory.

```env
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token
```

The PostgreSQL credentials are stored in the `.env` file of the `mcp-server` project.

Example:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=expense-tracker
DB_USER=postgres
DB_PASSWORD=your_postgres_password
```

Do not commit `.env` files to GitHub.

## Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
```

### 2. Move into the Client Directory

```bash
cd mcp-client
```

### 3. Create the Virtual Environment

```bash
uv venv
```

### 4. Activate the Environment on Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### 5. Install Dependencies

```bash
uv sync
```

## PostgreSQL Setup

Create a PostgreSQL database named:

```text
expense-tracker
```

Create the `transactions` table:

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    amount NUMERIC(12, 2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    transaction_type VARCHAR(20) NOT NULL
        CHECK (transaction_type IN ('expense', 'credit')),
    transaction_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

The expense MCP server uses this table to store both expenses and credits.

## Running the Application

Make sure PostgreSQL is running.

Then make sure the MCP server project is available at the path configured inside `client2.py`.

Run the Streamlit application:

```bash
uv run streamlit run client2.py
```

Streamlit will provide a local URL similar to:

```text
http://localhost:8501
```

Open the URL in your browser.

## How It Works

When a user enters a request, the Streamlit client sends the conversation to the Qwen model.

The model has access to the tools discovered from both MCP servers.

For example:

```text
Add an expense of Rs 200 for food.
```

The flow is:

```text
User
  ↓
Streamlit
  ↓
Qwen
  ↓
Tool Selection
  ↓
Expense MCP Server
  ↓
PostgreSQL
  ↓
Tool Result
  ↓
Qwen
  ↓
Final Response
  ↓
Streamlit
```

For an arithmetic request:

```text
What is 250 * 40?
```

The flow becomes:

```text
User
  ↓
Streamlit
  ↓
Qwen
  ↓
multiply tool
  ↓
Math MCP Server
  ↓
Result
  ↓
Qwen
  ↓
Final Response
```

## Multi-Server MCP

The client uses `MultiServerMCPClient` to connect to multiple MCP servers.

Conceptually, the configuration looks like:

```python
SERVERS = {
    "math": {
        "transport": "stdio",
        "command": "...",
        "args": [...]
    },
    "expense": {
        "transport": "stdio",
        "command": "...",
        "args": [...]
    }
}
```

This allows the LLM to access tools from both servers through a single client.

## Tool Calling

The LLM is first bound to the available MCP tools.

The tool-calling flow is:

```text
Qwen
  ↓
Tool Calls
  ↓
MCP Tools
  ↓
Tool Results
  ↓
Qwen
  ↓
Final Answer
```

The client executes the requested tools and then sends the tool results back to the model so that it can generate the final response.

## Async Architecture

The MCP tools and LLM calls use asynchronous execution.

The main message-processing flow is handled inside a single asynchronous function:

```text
process_message()
       │
       ├── get MCP tools
       │
       ├── call LLM
       │
       ├── execute MCP tools
       │
       └── call LLM for final response
```

The Streamlit application runs this flow through a single event loop for each user interaction.

This avoids repeatedly creating separate event loops for MCP and HTTP resources.

## Conversation History

The application maintains conversation history using LangChain message objects.

The history contains:

```text
SystemMessage
HumanMessage
AIMessage
ToolMessage
```

This allows the model to maintain context across multiple user messages during the Streamlit session.

### Example

```text
User:
Add Rs 500 for groceries.

Assistant:
Added an expense of Rs 500 for groceries.

User:
Show my expenses.

Assistant:
...
```

## Security

Sensitive credentials should never be committed to GitHub.

The `.gitignore` should contain:

```gitignore
.env
.venv/
__pycache__/
*.pyc
```

Never commit:

```text
.env
Hugging Face API tokens
PostgreSQL passwords
```

## Development Architecture

The client and server are intentionally separated.

```text
mcp-client
    │
    │ MCP protocol
    ▼
mcp-server
    │
    ▼
PostgreSQL
```

The client does not directly import the expense or math server functions.

Instead, communication happens through MCP.

This separation makes it possible to replace or add MCP servers without changing the core client architecture.

## Example Commands

### Expense

```text
Add an expense of Rs 250 for food.

Add an expense of Rs 1200 for shopping.

Show my expenses from 2026-09-01 to 2026-09-05.

Summarize my expenses.

Edit expense 3 and change the amount to Rs 500.

Delete expense 4.

Add a credit of Rs 50000 for salary.
```

### Math

```text
What is 25 + 75?

Calculate 1000 - 350.

Multiply 25 by 12.

Divide 1000 by 8.

Roll 5 dice.
```

### Combined Requests

The same assistant can handle different tool domains:

```text
What is 500 + 250?

Then add that amount as a food expense.
```

The LLM can use the appropriate MCP tools to perform the required operations.

## Future Improvements

Possible improvements for the project include:

- Expense analytics dashboard
- Monthly spending charts
- Category-wise visualization
- Budget tracking
- Spending alerts
- Recurring expenses
- Authentication
- User-specific expense data
- Better error handling
- MCP server health monitoring
- Persistent conversation storage
- Production deployment
- Dockerization
- CI/CD
- PostgreSQL connection pooling
- MCP server logging
- Tool execution tracing with LangSmith

## Learning Goals

This project demonstrates how to build an application using:

```text
LLM
 ↓
Tool Calling
 ↓
MCP
 ↓
Multiple MCP Servers
 ↓
Database
```

It also demonstrates the separation between:

- AI client
- MCP protocol
- MCP tools
- Backend logic
- Database

The project serves as a practical example of connecting an LLM application to multiple external capabilities through the Model Context Protocol.