import os
import requests
import time
from flask import Flask, request

app = Flask(__name__)

# Environment variables থেকে Token নেওয়া
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HUGGINGFACE_TOKEN = os.environ.get("HUGGINGFACE_TOKEN")

# একাধিক মডেল ব্যবহার করা যাবে (fallback এর জন্য)
MODELS = [
    "facebook/blenderbot-400M-distill",  # দ্রুত এবং ভালো
    "microsoft/DialoGPT-medium",  # backup
]

def send_message(chat_id, text):
    """টেলিগ্রামে মেসেজ পাঠানোর ফাংশন"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def send_typing_action(chat_id):
    """Typing indicator পাঠানোর ফাংশন"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendChatAction"
    data = {
        "chat_id": chat_id,
        "action": "typing"
    }
    try:
        requests.post(url, data=data, timeout=5)
    except:
        pass

def get_ai_response(user_message):
    """Hugging Face AI থেকে উত্তর পাওয়ার ফাংশন"""
    
    for model in MODELS:
        try:
            API_URL = f"https://api-inference.huggingface.co/models/{model}"
            headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
            
            payload = {
                "inputs": user_message,
                "parameters": {
                    "max_new_tokens": 100,
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "return_full_text": False
                },
                "options": {
                    "wait_for_model": True,
                    "use_cache": False
                }
            }
            
            # 60 সেকেন্ড পর্যন্ত অপেক্ষা করবে
            response = requests.post(
                API_URL, 
                headers=headers, 
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # বিভিন্ন response format handle করা
                if isinstance(result, list) and len(result) > 0:
                    if "generated_text" in result[0]:
                        return result[0]["generated_text"]
                    elif "text" in result[0]:
                        return result[0]["text"]
                elif isinstance(result, dict):
                    if "generated_text" in result:
                        return result["generated_text"]
                    elif "text" in result:
                        return result["text"]
                
            elif response.status_code == 503:
                # Model loading হচ্ছে, পরের model try করো
                print(f"Model {model} is loading, trying next...")
                continue
                
        except requests.Timeout:
            print(f"Timeout with model {model}, trying next...")
            continue
        except Exception as e:
            print(f"Error with model {model}: {str(e)}")
            continue
    
    # যদি সব model fail করে
    return "হ্যালো! আমি এখনও শিখছি। আপনি ইংরেজিতে প্রশ্ন করলে আরও ভালো উত্তর দিতে পারবো। 😊"

@app.route("/", methods=["POST"])
def telegram_webhook():
    """টেলিগ্রাম থেকে মেসেজ গ্রহণ করার ফাংশন"""
    try:
        data = request.get_json()
        
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            user_message = data["message"].get("text", "")
            
            if user_message:
                # Typing indicator দেখাও
                send_typing_action(chat_id)
                
                # বিশেষ commands handle করা
                if user_message.lower() in ["/start", "/help"]:
                    welcome_msg = (
                        "👋 হ্যালো! আমি একটি AI চ্যাটবট।\n\n"
                        "আমাকে যেকোনো প্রশ্ন করতে পারেন।\n"
                        "ইংরেজিতে লিখলে সবচেয়ে ভালো উত্তর পাবেন!\n\n"
                        "উদাহরণ:\n"
                        "- What is AI?\n"
                        "- Tell me a joke\n"
                        "- How are you?"
                    )
                    send_message(chat_id, welcome_msg)
                else:
                    # AI থেকে উত্তর নিন
                    ai_response = get_ai_response(user_message)
                    
                    # টেলিগ্রামে পাঠান
                    send_message(chat_id, ai_response)
        
        return "OK", 200
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return "Error", 500

@app.route("/")
def home():
    """Bot চালু আছে কিনা চেক করার জন্য"""
    return "✅ Bot is running! Send me a message on Telegram."

@app.route("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy", "bot": "online"}, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
