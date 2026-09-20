from google.adk.agents.llm_agent import Agent
from google.adk.agents.parallel_agent import ParallelAgent



instagram_agent = Agent(
    model='gemini-3.5-flash',
    name='instagram_agent',
    description='Instagram agent for creating instagram video script.',
    instruction='Based on user topics create  script for High SEO instagram reel',
)

linkedin_agent = Agent(
    model='gemini-3.5-flash',
    name='linkedin_agent',
    description='A helpful assistant for user linkedin post and branding.',
    instruction='Based on user topics create  post content for linkedin with High SEO and tags',
)

blog_agent = Agent(
    model='gemini-3.5-flash',
    name='blog_agent',
    description='A helpful assistant for creating medium blogs',
    instruction='based on user topics create a medium blog in 2000 words and high SEO Title',
)


social_media_agent = ParallelAgent(
    name='social_media_manager',
    sub_agents=[instagram_agent,linkedin_agent,blog_agent]
)

root_agent = social_media_agent


