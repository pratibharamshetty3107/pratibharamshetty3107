"""
TechTrapture Search App using Google Cloud Discovery Engine API
"""
from flask import Flask, render_template, request, jsonify
import subprocess
import json
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

# Google Cloud Discovery Engine Configuration
PROJECT_ID = "539049793214"
LOCATION = "us"
COLLECTION = "default_collection"
ENGINE_ID = "test_1779351562241"
SERVING_CONFIG = "default_search"

# Regional endpoint: "global" uses discoveryengine.googleapis.com,
# any other region uses "<region>-discoveryengine.googleapis.com"
API_HOST = (
    "discoveryengine.googleapis.com"
    if LOCATION == "global"
    else f"{LOCATION}-discoveryengine.googleapis.com"
)

def get_access_token():
    """Get Google Cloud access token"""
    try:
        result = subprocess.run(
            ['gcloud', 'auth', 'print-access-token'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting access token: {e}")
        return None

def search_query(query_text):
    """Perform search and get results"""
    token = get_access_token()
    if not token:
        return {"error": "Failed to get access token"}
    
    url = f"https://{API_HOST}/v1alpha/projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/engines/{ENGINE_ID}/servingConfigs/{SERVING_CONFIG}:search"
    
    payload = {
        "query": query_text,
        "pageSize": 10,
        "queryExpansionSpec": {"condition": "AUTO"},
        "spellCorrectionSpec": {"mode": "AUTO"},
        "languageCode": "en-GB",
        "userInfo": {"timeZone": "Asia/Calcutta"},
        "session": f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/engines/{ENGINE_ID}/sessions/-"
    }
    
    curl_command = [
        'curl', '-X', 'POST',
        '-H', f'Authorization: Bearer {token}',
        '-H', 'Content-Type: application/json',
        url,
        '-d', json.dumps(payload)
    ]
    
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Search error: {e}")
        return {"error": str(e)}

def get_answer(query_text, query_id, session_name):
    """Get generated answer for the query"""
    token = get_access_token()
    if not token:
        return {"error": "Failed to get access token"}
    
    url = f"https://{API_HOST}/v1alpha/projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/engines/{ENGINE_ID}/servingConfigs/{SERVING_CONFIG}:answer"
    
    payload = {
        "query": {
            "text": query_text,
            "queryId": query_id
        },
        "session": session_name,
        "relatedQuestionsSpec": {"enable": True},
        "answerGenerationSpec": {
            "ignoreAdversarialQuery": True,
            "ignoreNonAnswerSeekingQuery": False,
            "ignoreLowRelevantContent": True,
            "multimodalSpec": {},
            "includeCitations": True,
            "modelSpec": {"modelVersion": "gemini-2.5-flash/answer_gen/v1"}
        }
    }
    
    curl_command = [
        'curl', '-X', 'POST',
        '-H', f'Authorization: Bearer {token}',
        '-H', 'Content-Type: application/json',
        url,
        '-d', json.dumps(payload)
    ]
    
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Answer error: {e}")
        return {"error": str(e)}

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for search"""
    data = request.json
    query = data.get('query', '')
    
    print("\n" + "="*80)
    print("DEBUG: Raw query received from user:")
    print(f"  {query}")
    print("="*80)
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    # Step 1: Get search results
    search_results = search_query(query)
    
    if "error" in search_results:
        return jsonify(search_results), 500
    
    # Extract query ID and session from search results
    query_id = search_results.get('queryId', '')
    session_name = search_results.get('session', {}).get('name', '')
    
    print("\nDEBUG: Session data:")
    print(f"  Query ID: {query_id}")
    print(f"  Session Name: {session_name}")
    
    # Step 2: Get generated answer
    answer_query = f"{query} : keep answer max 100 words"
    print("\nDEBUG: Processed query sent to LLM:")
    print(f"  {answer_query}")
    print("="*80)
    
    answer_response = get_answer(answer_query, query_id, session_name)
    
    print("\nDEBUG: LLM Response:")
    print(json.dumps(answer_response, indent=2))
    print("="*80 + "\n")
    
    # Combine results
    response = {
        "query": query,
        "searchResults": search_results,
        "answer": answer_response
    }
    
    return jsonify(response)

if __name__ == '__main__':
    print("🚀 Starting TechTrapture Search App with Discovery Engine API...")
    print("📍 Server running at: http://localhost:8080")
    print("⌨️  Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=8080)
