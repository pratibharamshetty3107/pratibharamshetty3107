import vertexai
from vertexai import agent_engines

#pip install google-cloud-aiplatform[agent_engines,adk]

vertexai.init(project="gcai-sep-26", location="us-central1")

agent_engine = agent_engines.create(
    display_name="session-demo-engine",
)

print(agent_engine.gca_resource.name)


#https://console.cloud.google.com/agent-platform/runtimes/locations/us-central1/agent-engines/1236162781166698496/dashboard?project=gcai-sep-26