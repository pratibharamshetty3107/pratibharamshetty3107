from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

SERVER_URL = "https://pdf-image-mcp-server-115027786624.us-central1.run.app"

root_agent = Agent(
    model='gemini-3.5-flash',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='You are helpful assistant. help user with creating images and pdfs. Use the tools to generate images and pdfs as needed.',
        tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=f"{SERVER_URL}/mcp", timeout=120
            ),
            #header_provider=_auth_header,
        )
    ],
)
