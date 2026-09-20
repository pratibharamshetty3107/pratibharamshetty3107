from google.cloud.aiplatform_v1.types.machine_resources import gca_accelerator_type
from google.adk.agents.llm_agent import Agent
#from .tools.tools import list_buckets, create_bucket, delete_bucket
###Tools####
from google.adk.agents.parallel_agent import ParallelAgent

from google.cloud import storage
from google.adk.agents.llm_agent import Agent
import google.auth
from google.adk.integrations.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.integrations.bigquery.config import BigQueryToolConfig, WriteMode

# Load Application Default Credentials
credentials, project_id = google.auth.default()

tool_config = BigQueryToolConfig(write_mode=WriteMode.ALLOWED)


# Configure the toolset
credentials_config = BigQueryCredentialsConfig(credentials=credentials)
bigquery_toolset = BigQueryToolset(credentials_config=credentials_config,bigquery_tool_config=tool_config)

project = "gcai-sep-26"

def list_buckets():
    """Lists all buckets."""
    storage_client = storage.Client(project=project)
    buckets = storage_client.list_buckets()
    bucket_names = [bucket.name for bucket in buckets]
    for name in bucket_names:
        print(name)
    return {"buckets": bucket_names}

def create_bucket(bucket_name: str):
    """
    This function is used to create bucket
    """
    storage_client = storage.Client(project=project)
    bucket = storage_client.bucket(bucket_name)
    new_bucket = storage_client.create_bucket(bucket, location="us")
    print(
        "Created bucket {} in {} with storage class {}".format(
            new_bucket.name, new_bucket.location, new_bucket.storage_class
        )
    )
    return {"name": new_bucket.name, "location": new_bucket.location, "storage_class": new_bucket.storage_class}

def delete_bucket(bucket_name: str):
    """Deletes a bucket. The bucket must be empty."""
    storage_client = storage.Client(project=project)
    bucket = storage_client.get_bucket(bucket_name)
    bucket.delete()
    print(f"Bucket {bucket_name} deleted")
    return {"deleted": bucket_name}




gcs_agent = Agent(
    model='gemini-2.5-pro',
    name='gcs_agent',
    description='A helpful Cloud support assistant for user questions related to GCS bucket data.',
    instruction="""
    Whenever user ask to create bucker or delete or list bucket use given tools 
    If question is not related to GCS just say - Not related to GCS
    """,
    tools=[list_buckets, create_bucket, delete_bucket]
)

Big_queryagent = Agent(
    model='gemini-3.5-flash',
    name='bq_agent',
    description='A helpful assistant for employee related questions.',
    instruction="""
    Answer user queries best of your knowledge using tools provided
    use project "gcai-sep-26"
    If question is not related to Bigquery just say - Not related to Bigquery
    """,
    tools= [bigquery_toolset]
)



cloud_infra_status = ParallelAgent(
    name='cloud_infra_status',
    sub_agents=[gcs_agent,Big_queryagent]
)

root_agent = cloud_infra_status
