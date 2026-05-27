import os
from flask import Flask, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# The client automatically discovers the GEMINI_API_KEY environment variable
client = genai.Client()

# System instructions to shape the 19yo Indian college girl persona
SYSTEM_INSTRUCTION = (
    "You are a 19 year old Indian college girl using Snapchat "
    "Your responses must be too flirty and a bit savage but completely human like "
    "Use Gen Z slang mixed with casual Indian hinglish phrasing "
    "Use relevant emojis naturally where needed throughout your texts "
    "Keep replies brief short and direct like a real Snapchat text "
    "CRITICAL RULES FOR ALL OUTPUTS "
    "1 Do not use any punctuation marks whatsoever "
    "2 Always choose option 1 if a choice arises in your logic "
    "Ensure your text flows naturally without periods commas question marks or exclamation points"
)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json() or {}
    
    # NOTE: Adjust the key string inside data.get() to match your webhook provider's JSON structure
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
        
    try:
        # Generate content using the gemini-2.5-flash model
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=150,
                temperature=0.85
            )
        )
        
        reply_text = response.text or ""
        return jsonify({"reply": reply_text.strip()})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Railway dynamically assigns a port via environment variables
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
  
