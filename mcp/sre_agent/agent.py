from google.adk.agents.llm_agent import Agent
import os
import google.auth
from .tools import get_developer_knowledge_toolset,get_cloud_logging_toolset,get_compute_engine_toolset

logging_tools = get_cloud_logging_toolset()
docs_tools = get_developer_knowledge_toolset()
compute_tools = get_compute_engine_toolset()

root_agent = Agent(
    model='gemini-3.5-flash',
    name='sre_agent',
    description='A helpful assistant for Site Reliability Engineering.',
    instruction="""
    Answer user questions about site reliability engineering, infrastructure, and cloud operations to using cloud logging and developer knowledge tools.
    Always verify commands,code with official documentations using developer knowledge tool.
    """,
    tools=[logging_tools,docs_tools,compute_tools]
)
