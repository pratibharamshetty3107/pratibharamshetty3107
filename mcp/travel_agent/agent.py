import os

from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

# Google's managed remote MCP server (Maps Grounding Lite API: mapstools.googleapis.com)
MAPS_MCP_URL = "https://mapstools.googleapis.com/mcp"

maps_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=MAPS_MCP_URL,
        headers={"X-Goog-Api-Key": os.environ["GOOGLE_MAPS_API_KEY"]},
        timeout=30,
    ),
    # Expose only what a travel agent needs
    #tool_filter=["compute_routes", "search_places", "resolve_names", "lookup_weather"],
)

root_agent = Agent(
    model="gemini-2.5-flash",
    name="travel_direction_agent",
    description="Plans trips between two places using Google Maps.",
    instruction="""
    You are a travel direction assistant and use existing google maps tools to plan users holiday vacations .
    Use google maps tool to find places , distanbces , suggest itinary for trips.
   
    """,
    tools=[maps_toolset],
)
