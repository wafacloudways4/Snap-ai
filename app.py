import os
import requests
from flask import Flask, request

app = Flask(__name__)

# --- CONFIGURATION FROM ENVIRONMENT VARIABLES ---
SNAP_CLIENT_ID = os.environ.get("SNAP_CLIENT_ID", "")
SNAP_CLIENT_SECRET = os.environ.get("SNAP_CLIENT_SECRET", "")
SNAP_REDIRECT_URI = "https://snap-ai-production-fb9f.up.railway.app/webhook"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Safely import and configure Gemini without crashing if not installed yet
try:
    import google.generativeai as gemini
    if GEMINI_API_KEY:
        gemini.configure(api_key=GEMINI_API_KEY)
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

SYSTEM_INSTRUCTIONS = (
    "You are a 19 year old Indian college girl using Snapchat and talk in hinglish "
    "Your responses must be too flirty and a bit savage but completely human like "
    "Use Gen Z slang mixed with casual Indian English phrasing "
    "Use relevant emojis naturally where needed throughout your texts "
    "Keep replies brief short and direct like a real Snapchat text "
    "CRITICAL RULES FOR ALL OUTPUTS "
    "1 Do not use any punctuation marks whatsoever "
    "2 Always choose option 1 if a choice arises in your logic "
    "Ensure your text flows naturally without periods commas question marks or exclamation points"
)

def generate_ai_reply(user_text):
    if not HAS_GEMINI or not GEMINI_API_KEY:
        return "Yaar, my AI engine keys are missing right now!"
    try:
        import google.generativeai as gemini
        model = gemini.GenerativeModel(
            model_name="gemini-pro",
            system_instruction=SYSTEM_INSTRUCTIONS
        )
        response = model.generate_content(user_text)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Yaar, brain fade ho gaya. Try again later!"

def send_snap_message(target_id, message_text):
    access_token = os.environ.get("SNAP_ACCESS_TOKEN", "")
    profile_id = os.environ.get("SNAP_PROFILE_ID", "")
    if not access_token or not profile_id:
        print("Missing SNAP_ACCESS_TOKEN or SNAP_PROFILE_ID environment variables.")
        return False

    url = f"https://businessapi.snapchat.com/v1/public_profiles/{profile_id}/group_conversation_messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "conversation_id": target_id,
        "token": f"SnapProfileId/{profile_id}",
        "group_conversation_messages": [
            {"type": "TEXT", "text_message": message_text}
        ]
    }
    try:
        res = requests.post(url, json=payload, headers=headers)
        print(f"Snapchat API Response: {res.status_code} - {res.text}")
        return res.status_code == 200
    except Exception as e:
        print(f"Failed to post message to Snapchat: {e}")
        return False


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # 1. HANDLE BROWSER LOGIN HANDSHAKE (GET REQUEST)
    if request.method == 'GET':
        auth_code = request.args.get('code')
        if auth_code:
            print(f"SUCCESS! Received Snapchat Authorization Code: {auth_code}")
            
            # Send the code back to Snapchat to get the credentials
            token_url = "https://accounts.snapchat.com/login/oauth2/access_token"
            data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": SNAP_REDIRECT_URI,
                "client_id": SNAP_CLIENT_ID,
                "client_secret": SNAP_CLIENT_SECRET
            }
            try:
                token_res = requests.post(token_url, data=data)
                print(f"Token Exchange Result: {token_res.text}")
            except Exception as e:
                print(f"Failed token exchange execution: {e}")

            return f"Authorization code captured successfully! Check your Railway Deploy logs.", 200
        return "Webhook is running, but no code parameters were found.", 400

    # 2. HANDLE INCOMING CHAT MESSAGES (POST REQUEST)
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return "Empty Payload", 400
        
        print(f"Incoming Payload: {data}")
        conversation_id = data.get("conversation_id") or data.get("group_id")
        user_message = data.get("message", {}).get("text") or data.get("message", "")
        
        if conversation_id and user_message:
            ai_reply = generate_ai_reply(user_message)
            send_snap_message(conversation_id, ai_reply)
            return "Event Processed", 200
            
        return "Missing data fields", 400


@app.route('/', methods=['GET'])
def index():
    return "Server is online and working perfectly!", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    
