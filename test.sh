curl "https://generativelanguage.googleapis.com/v1beta/interactions" \
  -H 'Content-Type: application/json' \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -X POST \
  -d '{
    "model": "gemini-2.5-flash",
    "input": "Explain how AI works in a few words"
  }'


gs://tt-artifact-demo-00
adk deploy cloud_run --service_name="research-agent" --project=gcai-sep-26 --region=asia-south1 --adk_version=2.11.0 --port=8080  research_demo 
------
Agent Url - localhost
run - https://stratika-agent-ui-500297920251.asia-south1.run.app
create session api call -- create session
send msg --> 



# 1) agent is loaded
curl -s "https://bq-agent-ui-115027786624.asia-south1.run.app/list-apps"            

# 2) create a session
curl -s -X POST "https://bq-agent-ui-115027786624.asia-south1.run.app/apps/bq_agent/users/vishal/sessions/sess-1" \
  -H "Content-Type: application/json" -d '{}'

# 3) run the agent (real Vertex GenerateContent call)
curl -s -X POST "https://bq-agent-ui-115027786624.asia-south1.run.app/run" -H "Content-Type: application/json" -d '{
  "app_name": "bq_agent",
  "user_id": "vishal",
  "session_id": "sess-1",
  "new_message": {"role": "user", "parts": [{"text": "show me employees from engineering department"}]}
}'


# run sse
curl -s -X POST "https://bq-agent-ui-115027786624.asia-south1.run.app/run_sse" -H "Content-Type: application/json" -d '{
  "app_name": "bq_agent",
  "user_id": "vishal",
  "session_id": "sess-1",
  "new_message": {"role": "user", "parts": [{"text": "show me employees from finance department"}]}
}'
### Deployment

#without dev ui
adk deploy cloud_run --service_name="bq-agent" --project=gcai-sep-26 --region=asia-south1 bq_agent 

#with dev ui
adk deploy cloud_run --service_name="bq-agent-ui" --project=gcai-sep-26 --with_ui --region=asia-south1 bq_agent 

adk deploy gke  --project=gcai-sep-26 --region=asia-south1 --service_type=LoadBalancer --cluster_name=adk-demo --with_ui --service_name="bq-agent" bq_agent


### Agent Engine

adk deploy agent_engine --project=gcai-sep-26 --region=asia-south1  --trace_to_cloud --otel_to_cloud --display_name="bq_agent" bq_agent
 


## Creating GKE cluster
gcloud container clusters create adk-demo \
  --region=$REGION --node-locations=${REGION}-a --num-nodes=1 \
  --machine-type=e2-standard-4 \
  --network=sandbox-vpc --subnetwork=sandbox-vpc \
  --scopes=https://www.googleapis.com/auth/cloud-platform


## GKE deployment


TOKEN=$(gcloud auth print-identity-token)
#Create session

curl -X POST -H "Authorization: Bearer $TOKEN" \
    https://bq-agent-115027786624.asia-south1.run.app/apps/bq_agent/users/vishal/sessions/session_1 \
    -H "Content-Type: application/json"
#Ask query to agent

curl -X POST -H "Authorization: Bearer $TOKEN" \
    https://bq-agent-115027786624.asia-south1.run.app/run \
    -H "Content-Type: application/json" \
    -d '{
    "app_name": "bq_agent",
    "user_id": "vishal",
    "session_id": "session_1",
    "new_message": {
        "role": "user",
        "parts": [{
        "text": "How many employees are in the employee table?"
        }]
    },
    "streaming": false
    }'