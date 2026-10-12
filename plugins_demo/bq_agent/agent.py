from google.adk.agents.llm_agent import Agent
import google.auth
from google.adk.apps import App
from google.adk.integrations.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.integrations.bigquery.config import BigQueryToolConfig, WriteMode
from google.adk.plugins.logging_plugin import LoggingPlugin

# Load Application Default Credentials
credentials, project_id = google.auth.default()

tool_config = BigQueryToolConfig(write_mode=WriteMode.ALLOWED)
logging_plugin = LoggingPlugin()

# Configure the toolset
credentials_config = BigQueryCredentialsConfig(credentials=credentials)
bigquery_toolset = BigQueryToolset(credentials_config=credentials_config,bigquery_tool_config=tool_config)


bq_agent = Agent(
    model='gemini-3.5-flash',
    name='hr_agent',
    description='A helpful assistant for employee related questions.',
    instruction="""
    Answer employee questions based on the data available in Bigquery 
    table gcai-sep-26.adk_demo.employee.
    You can help user with write operations as well like create table,drop table
    """,
    tools= [bigquery_toolset]
)

app = App(
    name='bq_agent',
    root_agent=bq_agent,
    plugins=[logging_plugin]
)
