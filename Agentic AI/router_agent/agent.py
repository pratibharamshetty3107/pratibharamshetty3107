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


social_media_agent = Agent(
    name='social_media_manager',
    model='gemini-3.5-flash',
    instruction="""
    You are expert social media manager and you have access to three subagent for Instagranm,Linkedin
    blog writing. 
    Based on user request route control to respective subagent.
    If user does not mention platform instagram.linkedin or blog then ask user about platform confirmation

    STRICT RULE

    IF NOT SURE ABOUT SUBAGENT ALWAYS ASK USER
    """,
    sub_agents=[instagram_agent,linkedin_agent,blog_agent]
)

root_agent = social_media_agent


