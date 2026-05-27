import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as gemini

app = Flask(__name__)

# --- CONFIGURATION FROM ENVIRONMENT VARIABLES ---
# Make sure these are saved in your Railway "Variables" tab!
SNAP_CLIENT_ID = os.environ.get("SNAP_CLIENT_ID")
SNAP_CLIENT_SECRET = os.environ.get("SNAP_CLIENT_SECRET")
SNAP_REDIRECT_URI = "https://snap-ai-production-fb9f.up.railway.app/webhook"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configure Gemini Engine
if GEMINI_API_KEY:
    gemini.configure(api_key=GEMINI_API_KEY)

# --- SYSTEM PROMPT (19-year-old Indian Girl Persona) ---
SYSTEM_INSTRUCTIONS = (
    "You are a 19-year-old savage, witty Indian girl named Wafa. "
    "Use casual conversational language, mix in occasional Hindi/Urdu context naturally, "
    "keep your responses brief, grounded, and match the energy of the user."
)

def generate_ai_reply(user_text):
    """Generates a response using the Gemini API."""
    try:
        model = gemini.GenerativeModel(
            model_name="gemini-pro",
            system_instruction=SYSTEM_INSTRUCTIONS
        )
        response = model.generate_content(user_text)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Yaar, brain fade ho gaya. Try again later!"

def send_snap_message(target_id, message_text, is_group=False):
    """Sends a text message back to a user or a group chat via Snapchat API."""
    # Note: In production, you need to load your stored, valid access_token here
    access_token = os.environ.get("SNAP_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN")
    
    # Standard profile messaging URL template
    url = f"https://businessapi.snapchat.com/v1/public_profiles/{os.environ.get('SNAP_PROFILE_ID')}/group_conversation_messages"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "conversation_id": target_id,
        "token": f"SnapProfileId/{os.environ.get('SNAP_PROFILE_ID')}",
        "group_conversation_messages": [
            {
                "type": "TEXT",
                "text_message": message_text
            }
        ]
    }
    
    try:
        res = requests.post(url, json=payload, headers=headers)
        print(f"Snapchat API Response Code: {res.status_code}, Body: {res.text}")
        return res.status_code == 200
    except Exception as e:
        print(f"Failed to post message to Snapchat: {e}")
        return False


# --- THE MAIN WEBHOOK ROUTE (HANDLES BOTH GET AND POST) ---
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # 1. HANDLE BROWSER LOGIN HANDSHAKE (GET REQUEST)
    if request.method == 'GET':
        auth_code = request.args.get('code')
        if auth_code:
            print(f"SUCCESS! Received Snapchat Authorization Code: {auth_code}")
            
            # Code exchange logic to get your initial tokens
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
                # You can save tokens to a database, file, or print out to save to your Railway vars
            except Exception as e:
                print(f"Failed token exchange execution: {e}")

            return f"Authorization code captured successfully! Check your Railway Deploy logs.", 200
        return "Railway Webhook is active, but no code parameters were found.", 400

    # 2. HANDLE INCOMING CHAT MESSAGES (POST REQUEST)
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return "Empty Payload", 400
        
        print(f"Incoming Snapchat Webhook Payload: {data}")
        
        # Extract fields safely for both DMs and Group Chats (GCs)
        conversation_id = data.get("conversation_id") or data.get("group_id")
        user_message = data.get("message", {}).get("text") or data.get("message", "")
        
        if not conversation_id or not user_message:
            return "Missing mandatory message data fields", 400
            
        # Call Gemini to get the savage reply
        ai_reply = generate_ai_reply(user_message)
        
        # Send the message back out to the group or DM channel
        send_snap_message(conversation_id, ai_reply)
        
        return "Event Processed", 200


@app.route('/', methods=['GET'])
def index():
    return "Server is online and working perfectly!", 200

if __name__ == '__main__':
    # Listen on port provided by Railway environment
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
