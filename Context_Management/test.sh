adk web . --session_service_uri "postgresql+asyncpg://adkuser:adk_123@35.200.198.204:5432/adk_sessions"
adk web --session_service_uri=memory:// 
adk web --session_service_uri=agentengine://projects/115027786624/locations/us-central1/reasoningEngines/1236162781166698496

http:/127.0.0.1:8000/apps/session_demo/users/user/sessions
#Get session
curl -X GET http:/127.0.0.1:8000/apps/session_demo/users/user/sessions

#curl -X GET http:/127.0.0.1:8000/apps/session_demo/users/Vishal/sessions
#curl -X GET http:/127.0.0.1:8000/apps/session_demo/users/Vishal/sessions/2985262889335521280

#curl -X DELETE http:/127.0.0.1:8000/apps/session_demo/users/Vishal/sessions/2985262889335521280