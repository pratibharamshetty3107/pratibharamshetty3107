from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
import os
import google.auth
import google.auth.transport.requests

# Hosted GCP MCP servers (verified to expose a JSON-RPC /mcp endpoint).
DEVELOPER_KNOWLEDGE_MCP_URL = "https://developerknowledge.googleapis.com/mcp"
CLOUD_LOGGING_MCP_URL = "https://logging.googleapis.com/mcp"
COMPUTE_ENGINE_MCP_URL="https://compute.googleapis.com/mcp"


# GitHub's hosted MCP server (Copilot).

def _get_gcp_credentials():
    credentials, project_id = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_request = google.auth.transport.requests.Request()
    credentials.refresh(auth_request)
    return credentials, project_id


def get_developer_knowledge_toolset():
    api_key = os.getenv("DEVELOPER_KNOWLEDGE_API_KEY")
    if not api_key:
        raise ValueError("DEVELOPER_KNOWLEDGE_API_KEY not set in environment.")
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=DEVELOPER_KNOWLEDGE_MCP_URL,
            headers={"X-Goog-Api-Key": api_key},
        )
    )

def get_cloud_logging_toolset():
    credentials, project_id = _get_gcp_credentials()
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=CLOUD_LOGGING_MCP_URL,
            headers={
                "Authorization": f"Bearer {credentials.token}",
                "x-goog-user-project": project_id,
            },

        )
    )

def get_compute_engine_toolset():
    credentials, project_id = _get_gcp_credentials()
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=COMPUTE_ENGINE_MCP_URL,
            headers={
                "Authorization": f"Bearer {credentials.token}",
                "x-goog-user-project": project_id,
            },
        ),
        tool_filter=["list_instances"],

    )
