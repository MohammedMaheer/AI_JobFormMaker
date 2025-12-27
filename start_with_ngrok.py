import os
import sys
from app import app
from dotenv import load_dotenv

load_dotenv()

try:
    from pyngrok import ngrok
except ImportError:
    print("pyngrok not installed. Please run: pip install pyngrok")
    sys.exit(1)

def start_app_with_ngrok():
    # Set the port
    port = 5000
    
    # Check for auth token in env
    auth_token = os.environ.get("NGROK_AUTH_TOKEN")
    if auth_token:
        ngrok.set_auth_token(auth_token)
    
    try:
        public_url = ngrok.connect(port).public_url
    except Exception as e:
        # Check for auth error
        if "ERR_NGROK_4018" in str(e) or "authentication failed" in str(e):
            print("\n" + "!"*60)
            print(" NGROK AUTHENTICATION REQUIRED")
            print("!"*60)
            print("Ngrok now requires a free account.")
            print("1. Go to: https://dashboard.ngrok.com/signup")
            print("2. Copy your Authtoken.")
            print("-" * 60)
            
            try:
                token = input("Paste your Ngrok Authtoken here: ").strip()
                if token:
                    ngrok.set_auth_token(token)
                    public_url = ngrok.connect(port).public_url
                else:
                    print("No token provided. Exiting.")
                    return
            except Exception as inner_e:
                print(f"Failed to connect with token: {inner_e}")
                return
        else:
            print(f"Error starting ngrok: {e}")
            print("Ensure you don't have other ngrok instances running.")
            return

    print("\n" + "="*60)
    print(f" NGROK TUNNEL ESTABLISHED")
    print(f" Public URL: {public_url}")
    print(f" Webhook URL: {public_url}/api/webhook/application")
    print("="*60 + "\n")
    
    print("1. Copy the Webhook URL above.")
    print("2. Go to your Google Form Script Editor.")
    print("3. Paste it into the WEBHOOK_URL variable.")
    print("4. Save and Run setupTrigger.")
    print("\nStarting Flask Server...")
    
    # Run the app
    app.run(port=port, debug=False) # debug=True can cause double reloader issues with ngrok

if __name__ == '__main__':
    start_app_with_ngrok()
