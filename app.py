import json
import wikipediaapi
import re
import os
from flask import Flask, request, jsonify
from llmproxy import generate, pdf_upload  # Use llmproxy functions for generation and PDF upload

app = Flask(__name__)

# Fetch API keys from environment variables
end_point = os.environ.get("endPoint")  # Ensure these are set in your environment
api_key = os.environ.get("apiKey")  # Ensure these are set in your environment

# Initialize Wikipedia API
wiki_wiki = wikipediaapi.Wikipedia(
    language="en",
    user_agent="TuftsCSAdvisingBot/1.0 (danielheo@tufts.edu)"
)

class Chatbot:
    def __init__(self, session_id="TuftsAdvisingSession"):
        self.session_id = session_id
        self.upload_pdfs()

    def upload_pdfs(self):
        """Upload PDFs for retrieval-augmented generation (RAG)."""
        print("Uploading advising PDFs for retrieval...")
        pdf_upload("CompSci_LA_major.pdf", session_id=self.session_id, strategy='smart')  # Using pdf_upload function
        pdf_upload("CS_Course_Descriptions.pdf", session_id=self.session_id, strategy='smart')  # Using pdf_upload function
        print("PDFs uploaded. Ready to chat!\n")

    def ask_llm(self, query):
        """Ask the LLM while using RAG for retrieval where necessary."""
        response = generate(
            model="4o-mini",
            system="You are an AI academic advisor for Tufts CS students. Provide responses based on official guidelines.",
            query=query,
            temperature=0.7,
            lastk=3,
            session_id=self.session_id,
            rag_usage=True,
            rag_threshold=0.3,
            rag_k=5
        )

        # Extract chatbot response (removing unwanted metadata)
        chatbot_response = response.get("response", "").strip()

        # Ensure response is valid
        if chatbot_response and chatbot_response.lower() not in ["no valid response found.", "an error was encountered"]:
            return self.format_response(chatbot_response)

        return "❌ I couldn't find a direct answer. Try rewording your question or asking for more details."

    def format_response(self, response):
        """Format chatbot response for clean and readable console output."""
        formatted_response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)  # Remove **bold**
        formatted_response = formatted_response.replace("###", "").replace("\n\n", "\n")
        formatted_response = formatted_response.replace("\u2265", ">=")  # Fix Unicode issues (≥ symbol)

        # Remove unnecessary text after "Suggested Course Sequence"
        formatted_response = re.split(r"(### Additional Considerations|Additional Considerations)", formatted_response)[0]

        # Fix: Remove excessive whitespace and metadata
        formatted_response = formatted_response.strip()

        # Limit excessive text length (adjust max chars if needed)
        MAX_LEN = 10000
        if len(formatted_response) > MAX_LEN:
            formatted_response = formatted_response[:MAX_LEN] + "\n\n... [Response trimmed]"

        return formatted_response

    def get_response(self, query):
        """Process user query and return formatted chatbot response."""
        return self.ask_llm(query)  # Only returning cleaned response without extras

# Testing Route
@app.route('/test', methods=['GET'])
def test():
    return "Test endpoint working!"

@app.route('/', methods=['POST'])
def hello_world():
   return jsonify({"text": 'Hello from Koyeb - you reached the main page!'})

@app.route('/query', methods=['POST'])
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

    return jsonify({"text": response_text})

@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == '__main__':
    app.run(debug=True)
