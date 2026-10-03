adk web . --session_service_uri "postgresql+asyncpg://adkuser:adk_123@35.200.198.204:5432/adk_sessions"
adk web --session_service_uri=memory:// 
adk web --session_service_uri=agentengine://projects/115027786624/locations/us-central1/reasoningEngines/1236162781166698496

http:/127.0.0.1:8000/apps/session_demo/users/user/sessions
#Get session
curl -X GET http:/127.0.0.1:8000/apps/session_demo/users/user/sessions

#curl -X GET http:/127.0.0.1:8000/apps/session_demo/users/Vishal/sessions
#curl -X GET http:/127.0.0.1:8000/apps/session_demo/users/Vishal/sessions/2985262889335521280

#curl -X DELETE http:/127.0.0.1:8000/apps/session_demo/users/Vishal/sessions/2985262889335521280

#session short term memory - single chat
adk web -- ( store local sqlite database .adk folder)/ or postgress sql
chat 1 - remember
after restart also remember
chat 2 - will not remember

adk web inmemory
chat 1 - remember 
chat 2 - No 
after restrat  - No

adk vertex ai session
chat 1 - remember 
chat 2 - No 
after restart - remember 
---------

#memory long term memory - all chats for that user
adk web -- ( without session service)
chat 1 - remember
chat 2 - will not remember

adk web in memory
chat 1 - remember 
chat 2 - remember 
after restrat blank

adk vertex ai memory bank
chat 1 - remember 
chat 2 - remember 
after restart also - remember 
-----

adk web --memory_service_uri=agentengine://projects/115027786624/locations/us-central1/reasoningEngines/1236162781166698496


session/sesssion servive ---- session_id (chat window)--rememmber
memory / memory service --> user_id ( all chat window) -- remember all chats