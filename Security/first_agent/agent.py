from google.adk.agents.llm_agent import Agent
from google.adk.tools import google_search
from google.genai import types

root_agent = Agent(
    model='gemini-2.5-flash',
    name='my_agent',
    description='A helpful assistant for user questions.',
    instruction="""
    Answer user questions to the best of your knowledge .
    """,
    tools=[google_search],

)