from google.adk.agents.llm_agent import Agent
from google.adk.tools import preload_memory

async def auto_save_session_to_memory_callback(callback_context):
    print("################## Session Stored ###################")
    await callback_context.add_session_to_memory()

root_agent = Agent(
    model='gemini-3.5-flash',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
    tools=[preload_memory],
    after_agent_callback=auto_save_session_to_memory_callback,
)


