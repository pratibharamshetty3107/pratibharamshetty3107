from google.adk.agents.context import Context
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from typing import Dict, Any, Optional
from google.genai import types
from google import genai
import google.auth

def append_prompt(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    agent_name = callback_context.agent_name
    print("********checking LLM request schema********",llm_request)
    #Find the last user message
    last_user_message = ""
    if llm_request.contents and len(llm_request.contents) > 0:
        for content in reversed(llm_request.contents):
            if content.role == "user" and content.parts and len(content.parts) > 0:
                if hasattr(content.parts[0], "text") and content.parts[0].text:
                    last_user_message = content.parts[0].text
                    break

    print("=== MODEL REQUEST STARTED ===")
    print(f"Agent: {agent_name}")
    if last_user_message:
        print(f"User message: {last_user_message[:100]}...")

        # Prepend instructions to the last user message
        content_part = content.parts[0]
        instruction = "Please respond politely and also only give answer always in bullet points, avoid sending tables \n"
        content_part.text = instruction + content_part.text
        # Log the modified text
        print(f"Modified user message: {content_part.text[:150]}...")
        print("=== MODEL REQUEST COMPLETED ===")


    

def modify_output(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    Converts all text in the LLM response to uppercase.
    """
    if not llm_response or not llm_response.content or not llm_response.content.parts:
        return None

    for part in llm_response.content.parts:
        if hasattr(part, "text") and part.text:
            print(f"Original response part: {part.text}...")
            part.text = part.text.upper()  # convert to uppercase

    return llm_response  # return modified response


def check_token_limit(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Before model callback to check if input token count is less than 100.
    Roughly calculates token count using 4 characters = 1 token without making any extra LLM calls.
    If token count < 100, allows the request (returns None).
    Otherwise, prints token limit exceeded message and returns an LlmResponse.
    """
    
    session = callback_context._invocation_context.session
    print("****Session startes",session)
    print("*** ✅ ✅ ✅ checking llm request ****")
    print(llm_request.contents)
    print("*** ✅ ✅ ✅ ending llm request ****")
    input_text = ""
    if llm_request.contents:
        for content in llm_request.contents:
            if content.parts:
                for part in content.parts:
                    if hasattr(part, "text") and part.text:
                        input_text += part.text + " "

    # Roughly calculate token count (4 characters = 1 token)
    token_count = len(input_text) // 4

    print(f"=== INPUT TOKEN CHECK ===")
    print(f"Input characters: {len(input_text)}")
    print(f"Estimated token count (4 chars/token): {token_count}")

    if token_count < 100:
        print(f"✅ Token count ({token_count}) is less than 100. Allowing model request.")
        return None
    else:
        print(f"❌ Token limit exceeded: {token_count} tokens (limit is 100). Request blocked.")
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text=f"Token limit exceeded: Estimated input token count ({token_count}) exceeds the limit of 100 tokens."
                    )
                ],
            )
        )

# Users who get gemini-2.5-pro; everyone else gets gemini-2.5-flash.
PRO_USERS = {"vishal"}


def route_model_by_user(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Before model callback to pick the Gemini model based on user_id.
    Overrides llm_request.model, which is what ADK sends to Gemini.
    """
    user_id = callback_context.user_id
    model = "gemini-2.5-pro" if user_id in PRO_USERS else "gemini-2.5-flash"
    print(f"=== MODEL ROUTING: user={user_id} default={llm_request.model} -> {model} ===")
    llm_request.model = model
    return None
