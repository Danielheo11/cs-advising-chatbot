import os
import wikipediaapi
import re
from flask import Flask, request, jsonify, render_template
from typing import Optional  # Ensures compatibility with Python 3.9
from llmproxy import generate  # Import generate from llmproxy

# Fetch API keys from environment variables
end_point = os.environ.get("END_POINT")  # Make sure to set this in Koyeb
api_key = os.environ.get("API_KEY")  # Make sure to set this in Koyeb

# Initialize Wikipedia API
wiki_wiki = wikipediaapi.Wikipedia(
    language="en",
    user_agent="TuftsCSAdvisingBot/1.0 (danielheo@tufts.edu)"
)

app = Flask(__name__)

class Chatbot:
    def __init__(self, session_id="TuftsAdvisingSession"):
        self.session_id = session_id
        self.upload_pdfs()

    def upload_pdfs(self):
        """Upload PDFs for retrieval-augmented generation (RAG)."""
        print("Uploading advising PDFs for retrieval...")
        self.pdf_upload("CompSci_LA_major.pdf", session_id=self.session_id, strategy='smart')
        self.pdf_upload("CS_Course_Descriptions.pdf", session_id=self.session_id, strategy='smart')
        print("PDFs uploaded. Ready to chat!\n")

    def generate(self, model: str, system: str, query: str, temperature: Optional[float] = None, lastk: Optional[int] = None,
                 session_id: Optional[str] = None, rag_threshold: Optional[float] = 0.3, rag_usage: Optional[bool] = False,
                 rag_k: Optional[int] = 5):
        """Generate response using the model via llmproxy."""
        response = generate(
            model=model,
            system=system,
            query=query,
            temperature=temperature,
            lastk=lastk,
            session_id=session_id,
            rag_threshold=rag_threshold,
            rag_usage=rag_usage,
            rag_k=rag_k
        )

        return response

    def ask_llm(self, query):
        """Ask the LLM while using RAG for retrieval where necessary."""
        response = self.generate(
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

        chatbot_response = response.get("response", "").strip()

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

        formatted_response = formatted_response.strip()

        MAX_LEN = 10000
        if len(formatted_response) > MAX_LEN:
            formatted_response = formatted_response[:MAX_LEN] + "\n\n... [Response trimmed]"

        return formatted_response

    def get_response(self, query):
        """Process user query and return formatted chatbot response."""
        return self.ask_llm(query)  # Only returning cleaned response without extras

# Initialize the chatbot
chatbot = Chatbot()

@app.route('/')
def home():
    return render_template("index.html")  # This serves the frontend HTML page

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Get chatbot response
    response = chatbot.get_response(user_message)

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
