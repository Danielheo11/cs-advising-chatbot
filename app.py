import json
import os
import re
import requests
from flask import Flask, request, jsonify
from llmproxy import generate, pdf_upload  # Assuming these functions are correctly defined

app = Flask(__name__)

# Fetch API keys from environment variables
end_point = os.environ.get("endPoint")  # Ensure these are set in your environment
api_key = os.environ.get("apiKey")  # Ensure these are set in your environment

# Rocketchat credentials
ROCKETCHAT_URL = "https://chat.genaiconnect.net/direct/6N5ZduGQWJJXSEqXYzzWcNaJFCWDLjWp8J"
BOT_TOKEN = "WAxcUQUshcuvyYe-q0AXMXR7cSh31tpYxliLEBU6gHX"
BOT_USER_ID = "zzWcNaJFCWDLjWp8J"

# Function to send a message
def send_message(room_id, text):
    url = f"{ROCKETCHAT_URL}/chat.postMessage"
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": BOT_TOKEN,
        "X-User-Id": BOT_USER_ID
    }
    data = {
        "channel": room_id,
        "text": text
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# Function to simulate typing
def typing_indication(room_id):
    url = f"{ROCKETCHAT_URL}/livechat/typing"
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": BOT_TOKEN,
        "X-User-Id": BOT_USER_ID
    }
    data = {
        "roomId": room_id,
        "typing": True
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# Function to handle incoming messages and trigger actions
def handle_incoming_message(message, room_id):
    if message.lower() == "help":
        send_message(room_id, "How can I assist you today? :grinning:")  # Added emoji
    elif message.lower() == "info":
        send_message(room_id, "Here’s the info you requested! :book:")  # Added emoji
    else:
        send_message(room_id, "Let me get back to you shortly! :hourglass_flowing_sand:")
        typing_indication(room_id)  # Simulate typing
        # After processing, send a response to user
        send_message(room_id, "Here’s the info you requested! :information_desk_person:")

@app.route('/test', methods=['GET'])
def test():
    return "Test endpoint working! :white_check_mark:"

@app.route('/', methods=['POST'])
def query():
    # Log the complete incoming data to ensure it hits this route
    data = request.get_json()
    print(f"Data received: {json.dumps(data, indent=2)}")  # Log the complete data

    # Extract relevant information
    user = data.get("user_name", "Unknown")
    message = data.get("text", "")
    
    # Handle case where message is missing
    if not message:
        return jsonify({"status": "ignored", "message": "No message received"})
    
    print(f"Message from {user}: {message}")  # Log the message to verify it's being processed

    # Generate a response using LLMProxy
    response = generate(
        model="4o-mini",
        system="You are an AI academic advisor for Tufts CS students. Provide responses based on official guidelines.",
        query=message,
        temperature=0.0,
        lastk=0,
        session_id="GenericSession"
    )

    # Log the response from the LLM
    print(f"Response from LLM: {json.dumps(response, indent=2)}")  # Log the full response
    
    response_text = response.get('response', 'No valid response found.')
    print(f"Final Response: {response_text}")  # Log the final response that will be sent

    # Add some emoji to the response for a more friendly tone
    response_text = f"{response_text} :smiley:"

    return jsonify({"text": response_text})

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Not Found :mag_right:"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
