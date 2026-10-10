from google.adk.agents.context import Context
from google.genai import types

def check_access(callback_context: Context):
    session = callback_context._invocation_context.session
    #print(f"************callback result *********",session)
    user = session.user_id
    hr_team = ["raj","vishal"]
    if user in hr_team:
       print("✅ [callback] User {user} is authorized to access this application")
       return None
    else:
        print (f"❌ [callback] User {user} is not authorized to access this application")
        return types.Content(
            parts=[types.Part(text=f"You do not have access to HR Agent, user {user} is not in HR team")],
            role="model"  
        )

def log_completion(callback_context: Context):
    print("""""*** Completion ***""")
    session = callback_context._invocation_context.session
    print("********************************",session)
    


        

    