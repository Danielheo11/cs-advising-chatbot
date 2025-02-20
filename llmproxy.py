import os
import json
import requests

# Read proxy config from environment
end_point = os.environ.get("ENDPOINT")  # Ensure the environment variable name is correct
api_key = os.environ.get("API_KEY")     # Ensure the environment variable name is correct

def generate(
    model: str,
    system: str,
    query: str,
    temperature: Optional[float] = None,
    lastk: Optional[int] = None,
    session_id: Optional[str] = None,
    rag_threshold: Optional[float] = 0.5,
    rag_usage: Optional[bool] = False,
    rag_k: Optional[int] = 0
):
    headers = {
        'x-api-key': api_key
    }

    request = {
        'model': model,
        'system': system,
        'query': query,
        'temperature': temperature,
        'lastk': lastk,
        'session_id': session_id,
        'rag_threshold': rag_threshold,
        'rag_usage': rag_usage,
        'rag_k': rag_k
    }

    msg = None

    try:
        response = requests.post(end_point, headers=headers, json=request)

        if response.status_code == 200:
            res = json.loads(response.text)
            msg = {'response': res['result'], 'rag_context': res['rag_context']}
        else:
            msg = f"Error: Received response code {response.status_code}"
    except requests.exceptions.RequestException as e:
        msg = f"An error occurred: {e}"
    return msg
