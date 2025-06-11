The following is a coding reference guide for LLM coding agents, distilling the essence of the Model Context Protocol (MCP) and its implementation.

## Model Context Protocol (MCP) for LLM Coding Agents

### 1. What is MCP?

The Model Context Protocol (MCP) is a **standardized, secure, real-time, two-way communication interface** enabling AI systems (LLMs, AI-driven IDEs) to **connect with external tools, API services, and data sources**.

**Analogy:** Think of MCP as a **USB-C port for AI**. It allows a single, standardized way for AI models to interact with diverse external systems, unlike traditional APIs that require separate integration for each service.

**Key Advantages over Traditional APIs:**

| Feature               | MCP                               | Traditional API                 |
| :-------------------- | :-------------------------------- | :------------------------------ |
| **Integration Effort** | Single, standardized integration  | Separate integration per API    |
| **Real-Time Comm.** | ✅ Yes                            | ❌ No                           |
| **Dynamic Discovery** | ✅ Yes                            | ❌ No                           |
| **Scalability** | Easy (plug-and-play)              | Requires additional integrations |
| **Security & Control** | Consistent across tools           | Varies by API                   |

MCP's two-way communication allows AI models to **retrieve information and dynamically trigger actions**, facilitating intelligent and context-aware applications.

### 2. MCP Architecture Components:

* **Hosts:** Applications (e.g., AI-driven IDEs like Cursor) that require access to external data or tools.
* **Clients:** Maintain dedicated, one-to-one connections with MCP servers.
* **MCP Servers:** Lightweight servers exposing specific functionalities via MCP, connecting to local or remote data sources.
* **Local Data Sources:** Files, databases, or services securely accessed by MCP servers.
* **Remote Services:** External internet-based APIs or services accessed by MCP servers.

### 3. How MCP Components Interact (Practical Example):

1.  **Host (e.g., Cursor IDE)** sends a request to its MCP client to perform an action (e.g., update Google Sheet, send Slack notification).
2.  **MCP Client** connects to relevant **MCP Servers** (e.g., Google Sheets MCP server, Slack MCP server).
3.  **MCP Servers** interact with their respective **Remote Services** (e.g., Google Sheets API, Slack API) to execute the action.
4.  **MCP Servers** send responses back to the **MCP Client**.
5.  **MCP Client** forwards responses to the **Host**, which displays the result.

### 4. Building an MCP Server (Python SDK Guide for LLM Agents):

**Target:** Exposing custom functionalities (tools) and data (resources) to an LLM agent via an MCP server.

**Prerequisites:** Python installed.

**Step-by-step Guide:**

#### 4.1. Work Environment Setup:

1.  **Create Project Directory:**
    ```bash
    mkdir MCP_Server_Project
    cd MCP_Server_Project
    ```
2.  **Create Virtual Environment:**
    ```bash
    python -m venv venv
    ```
3.  **Activate Virtual Environment:**
    * **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    * **Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```
    (Ensure `(venv)` appears in your terminal prompt, indicating activation.)
4.  **Install MCP SDK and CLI:**
    ```bash
    pip install mcp mcp[cli]
    ```

#### 4.2. Writing the Server Code (`server.py`):

Create a Python file (e.g., `server.py`) and populate it with your MCP server logic.

**Core Structure:**

```python
# server.py
from mcp.server.fastmcp import FastMCP
import math

# Instantiate an MCP server client with a descriptive name
mcp = FastMCP("MyAwesomeMCP")

# DEFINE TOOLS: Functions exposed to the LLM agent
# Use the @mcp.tool() decorator to register functions as tools.
# Provide type hints for arguments and return values for clarity and validation.
# Add a docstring to describe the tool's purpose; this will be available to the LLM.

@mcp.tool()
def add(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtracts two numbers."""
    return a - b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiplies two numbers."""
    return a * b

@mcp.tool()
def divide(a: int, b: int) -> float:
    """Divides two numbers. Handles division by zero implicitly by Python's error handling, but you could add explicit checks."""
    return a / b

@mcp.tool()
def power(base: int, exponent: int) -> int:
    """Calculates the power of a base number raised to an exponent."""
    return base ** exponent

@mcp.tool()
def square_root(number: int) -> float:
    """Calculates the square root of a number."""
    if number < 0:
        raise ValueError("Cannot calculate square root of a negative number.")
    return math.sqrt(number)

@mcp.tool()
def factorial(n: int) -> int:
    """Calculates the factorial of a non-negative integer."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    return math.factorial(n)

# DEFINE RESOURCES: Dynamic data accessible by the LLM agent
# Use the @mcp.resource("resource_name://{param}") decorator.
# The URL-like string defines how the resource is addressed.
# Parameters in curly braces become arguments to the decorated function.

@mcp.resource("greeting://{name}")
def get_personalized_greeting(name: str) -> str:
    """Gets a personalized greeting for a given name."""
    return f"Hello, {name}!"

@mcp.resource("config://app_version")
def get_app_version() -> str:
    """Retrieves the current application version."""
    return "1.0.0"

# Main execution block: Starts the MCP server
if __name__ == "__main__":
    # 'transport="stdio"' enables communication over standard input/output,
    # suitable for development and certain integrations.
    mcp.run(transport="stdio")
```

**Code Explanation for LLM Agents:**

* **`FastMCP("MyAwesomeMCP")`**: Initializes the MCP server. The string "MyAwesomeMCP" is a human-readable name for the server.
* **`@mcp.tool()`**: This decorator registers a Python function as an MCP tool. LLM agents can "discover" and "call" these tools.
    * **Function Signature:** The function name (`add`, `subtract`, etc.) becomes the tool's identifier. Type hints (`a: int, b: int -> int`) are crucial for LLM agents to understand the input types, expected output, and for MCP to perform validation.
    * **Docstrings:** The docstring within each tool function (`"""Adds two numbers"""`) is vital. LLMs use these docstrings to understand *what the tool does* and when to use it, enabling intelligent tool selection.
* **`@mcp.resource("greeting://{name}")`**: This decorator registers a function as an MCP resource. Resources expose data to the LLM agent.
    * **Resource URL (`greeting://{name}`):** Defines the structure for accessing the resource. The `{name}` part indicates a dynamic parameter that the LLM agent needs to provide.
    * **Function Signature:** Similar to tools, type hints are important.
* **`mcp.run(transport="stdio")`**: This starts the MCP server, making it ready to accept connections and process requests. `transport="stdio"` is a common setup for local development and integration with tools that support `stdio` communication.

#### 4.3. Running & Testing the Server Locally (MCP Inspector):

**Purpose:** To verify your MCP server's functionality independently before integrating with an LLM agent.

1.  **Start the MCP Server:**
    Open your terminal within the virtual environment (where `server.py` is located) and run:
    ```bash
    python server.py
    ```
    This will start your MCP server. Keep this terminal window open.
2.  **Launch MCP Inspector CLI:**
    Open a *new* terminal window (also within the activated virtual environment) and run:
    ```bash
    mcp inspect
    ```
    This will typically output a URL (e.g., `http://localhost:5000` or similar).
3.  **Open MCP Inspector in Browser:**
    Navigate to the provided URL in your web browser.
4.  **Connect:**
    On the MCP Inspector page, click "Connect". You should see a successful connection.
5.  **Test Resources:**
    * Go to the "Resources" tab.
    * Click "List Templates".
    * Select `greeting://{name}`.
    * Enter a `name` (e.g., "AI Agent").
    * Click "Read Resource". You should see the personalized greeting.
6.  **Test Tools:**
    * Go to the "Tools" tab.
    * Click "List Tools".
    * Select a tool (e.g., `add`).
    * Input values for the parameters (e.g., `a=5`, `b=3`).
    * Click "Run Tool". You should see the calculated output.

### 5. Connecting Custom MCP Servers to LLM IDEs/Agents (e.g., Cursor):

**General Concept:** LLM-powered IDEs and agents typically have a configuration section to "add new servers" or "connect to external tools." For MCP, this usually involves providing the command to run your MCP server.

**Example (Cursor IDE Integration):**

1.  **Open Project in IDE:** Open the directory containing your `server.py` in your chosen LLM-integrated IDE (e.g., Cursor).
2.  **Activate Virtual Environment (within IDE terminal):** It's good practice to activate your `venv` within the IDE's integrated terminal.
    * Windows: `.\venv\Scripts\activate`
    * Linux/macOS: `source venv/bin/activate`
3.  **Configure New MCP Server in IDE Settings:**
    * Navigate to `File` -> `Preferences` -> `[IDE Name] Settings` (e.g., `Cursor Settings`).
    * Search for "MCP" settings.
    * Select "Add New Server".
    * **Name:** Give your server a meaningful name (e.g., "My Custom Calculator").
    * **Type:** Select "command".
    * **Command:** Provide the full path to your Python executable within the virtual environment, followed by the full path to your MCP server script.
        * **Format:** `/path/to/your/venv/bin/python /path/to/your/server.py`
        * **Example (Windows):** `C:\Users\YourUser\MCP_Server_Project\venv\Scripts\python.exe C:\Users\YourUser\MCP_Server_Project\server.py`
        * **Example (Linux/macOS):** `/home/youruser/MCP_Server_Project/venv/bin/python /home/youruser/MCP_Server_Project/server.py`
4.  **Verify Connection:**
    * After saving the settings, your IDE should indicate the server's status (e.g., a green circle next to the server name).
    * **Test with LLM Agent:** In the IDE's chat/composer window, select the LLM agent and prompt it to use your defined tools.
        * **Prompt Example:** "Can you add 10 and 5 using the calculator tool?"
        * The LLM agent should identify and call the `add` tool (often aliased as `mcp_add()`).

### 6. Composio MCP (Pre-built Integrations for LLM Agents):

For complex, common integrations (e.g., Google Drive, Slack, Linear), Composio MCP provides pre-built, managed MCP servers. This simplifies integration to a "single line of code" (or rather, a configuration step).

**Integration Steps (Conceptual for LLM Agents):**

1.  **Browse Composio MCP Directory:** Find the desired tools/services (e.g., Linear, Slack).
2.  **Generate SSE Key/URL:** Composio provides a unique URL for the pre-built MCP server.
3.  **Configure in LLM IDE/Agent Settings:**
    * Go to the MCP server settings in your IDE.
    * **Type:** Select "sse" (Server-Sent Events).
    * **Server URL:** Paste the URL generated by Composio.
4.  **Authenticate (OAuth):** For services requiring authentication (like Slack or Linear), the LLM agent will guide you through an OAuth flow to grant necessary permissions.
5.  **Use with LLM Agent:** Once connected and authenticated, your LLM agent can directly use the functionalities exposed by the Composio MCP server (e.g., "Create a Linear issue and send a Slack notification about it").

**Key takeaway for LLM Agents:** Composio MCP abstracts away the server management and API integration complexities, allowing the agent to immediately access a rich set of tools and services.

### Conclusion for LLM Agents:

MCP is a foundational protocol for enabling LLM agents to transcend their internal knowledge and **interact seamlessly with the real world** through external tools and data. By understanding how to build custom MCP servers (for specialized functionalities) and leverage pre-built solutions like Composio MCP (for common integrations), LLM coding agents can significantly enhance their capabilities in:

* **Automation:** Triggering actions in external systems.
* **Contextual Awareness:** Retrieving real-time data from various sources.
* **Workflow Integration:** Becoming an integral part of developer workflows within IDEs.

Mastering MCP will be crucial for LLM agents aiming to become truly intelligent and useful participants in software development and beyond.