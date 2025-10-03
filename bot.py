import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Environment variables থেকে Token নেওয়া (নিরাপদ পদ্ধতি)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HUGGINGFACE_TOKEN = os.environ.get("HUGGINGFACE_TOKEN")

# Hugging Face Model (ইংরেজিতে চ্যাট করার জন্য ভালো মডেল)
HF_MODEL = "microsoft/DialoGPT-medium"

def send_message(chat_id, text):
    """টেলিগ্রামে মেসেজ পাঠানোর ফাংশন"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, data=data)

def get_ai_response(user_message):
    """Hugging Face AI থেকে উত্তর পাওয়ার ফাংশন"""
    API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
    
    payload = {
        "inputs": user_message,
        "parameters": {
            "max_length": 100,
            "temperature": 0.7
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "দুঃখিত, আমি বুঝতে পারিনি।")
        else:
            return "দুঃখিত, এই মুহূর্তে উত্তর দিতে পারছি না।"
    except Exception as e:
        return f"Error: {str(e)}"

@app.route("/", methods=["POST"])
def telegram_webhook():
    """টেলিগ্রাম থেকে মেসেজ গ্রহণ করার ফাংশন"""
    data = request.get_json()
    
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_message = data["message"].get("text", "")
        
        if user_message:
            # AI থেকে উত্তর নিন
            ai_response = get_ai_response(user_message)
            
            # টেলিগ্রামে পাঠান
            send_message(chat_id, ai_response)
    
    return "OK", 200

@app.route("/")
def home():
    """Bot চালু আছে কিনা চেক করার জন্য"""
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
