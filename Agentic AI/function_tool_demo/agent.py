from google.adk.agents.llm_agent import Agent
#from .tools.tools import list_buckets, create_bucket, delete_bucket
from .tools import list_buckets, create_bucket, delete_bucket

root_agent = Agent(
    model='gemini-2.5-pro',
    name='cloud_agent',
    description='A helpful Cloud support assistant for user questions related to GCS bucket data.',
    instruction="""
    Answer user questions to the best of your knowledge
    You also have access to three GCS tools use them to answer users questions about GCS
    before deleting any bucket ask for user confirmation
    Give responses in proper bullet points or tabular format
    """,
    tools=[list_buckets, create_bucket, delete_bucket]
)
