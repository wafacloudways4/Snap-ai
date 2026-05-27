import os
import requests
from flask import Flask, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# Initialize the Gemini AI engine using your key automatically
client = genai.Client()

# System instructions to shape the 19yo Indian college girl persona
SYSTEM_INSTRUCTION = (
    "You are a 19 year old Indian college girl using Snapchat speak in hinglish"
    "Your responses must be too flirty and a bit savage but completely human like "
    "Use Gen Z slang mixed with casual Indian hinglish phrasing "
    "Use relevant emojis naturally where needed throughout your texts "
    "Keep replies brief short and direct like a real Snapchat text "
    "CRITICAL RULES FOR ALL OUTPUTS "
    "1 Do not use any punctuation marks whatsoever "
    "2 Always choose option 1 if a choice arises in your logic "
    "Ensure your text flows naturally without periods commas question marks or exclamation points"
)

# Fetch your secure credentials from Railway configuration variables
CLIENT_ID = os.environ.get("SNAP_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SNAP_CLIENT_SECRET")
# A placeholder for your permanent refresh token generated during Step 4
REFRESH_TOKEN = os.environ.get("SNAP_REFRESH_TOKEN")

def get_active_access_token():
    """Contact Snapchat to exchange the permanent refresh token for a 1-hour access token"""
    token_url = "https://accounts.snapchat.com/login/oauth2/access_token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    try:
        response = requests.post(token_url, data=payload)
        return response.json().get("access_token")
    except Exception as e:
        print(f"Token error: {str(e)}")
        return None

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json() or {}
    user_message = data.get("message", "")
    profile_id = data.get("profile_id", "") # Sent by incoming webhook
    conversation_id = data.get("conversation_id", "") # Sent by incoming webhook
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
        
    try:
        # 1. Ask Gemini to generate the flirty/savage reply
        ai_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=100,
                temperature=0.85
            )
        )
        reply_text = (ai_response.text or "").strip()
        
        # 2. Grab a fresh Snapchat permission token
        active_token = get_active_access_token()
        if not active_token:
            return jsonify({"error": "Snapchat Auth Failed"}), 401
            
        # 3. [span_1](start_span)Deliver the response text directly back into the Snapchat conversation
        snap_api_url = f"https://businessapi.snapchat.com/v1/public_profiles/{profile_id}/group_conversation_messages"[span_1](end_span)
        headers = {
            "Authorization": f"Bearer {active_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "profile_id": profile_id,
            "conversation_id": conversation_id,
            "token": f"SnapProfileId/{profile_id}",
            "group_conversation_messages": [
                {
                    "type": "TEXT",
                    "text_message": reply_text
                }
            ]
        }
        
        requests.post(snap_api_url, json=payload, headers=headers)
        return jsonify({"status": "success", "sent": reply_text})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
