from google.adk.agents.llm_agent import Agent
from google.adk.plugins.bigquery_agent_analytics_plugin import BigQueryAgentAnalyticsPlugin
from google.adk.apps import App
from google.adk.plugins.save_files_as_artifacts_plugin import SaveFilesAsArtifactsPlugin
from  google.adk.plugins.context_filter_plugin import ContextFilterPlugin
bqplugin = BigQueryAgentAnalyticsPlugin(
    project_id="gcai-sep-26",
    dataset_id="agent_analytics",
)

artifact_plugin = SaveFilesAsArtifactsPlugin()
context_filter_plugin = ContextFilterPlugin(num_invocations_to_keep=2)


root_agent = Agent(
    model='gemini-3.5-flash',
    name='root_agent',
    description='A helpful assistant for user questions based on document provided',
    instruction='Answer user questions to the best of your knowledge based on document or data provided',
)

app = App(
    name='artifact_plugin_demo',
    root_agent=root_agent,
    plugins=[bqplugin,artifact_plugin],
)