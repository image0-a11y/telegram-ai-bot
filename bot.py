import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Environment variables থেকে Token নেওয়া
TELEGRAM_TOKEN = os.environ.get("7903219090:AAH91uNk38i8TDGl2YwP7o1h8jt6uNZZWus")
GEMINI_API_KEY = os.environ.get("AIzaSyBwvBgDDgBPvwDqT7Funy3RDApzLoRbdI8")

def send_message(chat_id, text):
    """টেলিগ্রামে মেসেজ পাঠানোর ফাংশন"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def send_typing_action(chat_id):
    """Typing indicator পাঠানোর ফাংশন"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendChatAction"
    data = {
        "chat_id": chat_id,
        "action": "typing"
    }
    try:
        requests.post(url, json=data, timeout=5)
    except:
        pass

def get_gemini_response(user_message):
    """Google Gemini AI থেকে উত্তর পাওয়ার ফাংশন"""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": user_message
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500,
            "topP": 0.95,
        }
    }
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Gemini Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Response থেকে text বের করা
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return parts[0]["text"].strip()
            
            return "দুঃখিত, আমি উত্তর তৈরি করতে পারিনি।"
        
        elif response.status_code == 400:
            error_data = response.json()
            print(f"API Error: {error_data}")
            return "❌ Invalid request. অনুগ্রহ করে আপনার প্রশ্ন আবার লিখুন।"
        
        elif response.status_code == 429:
            return "⏱️ অনেক বেশি request হয়ে গেছে। একটু পরে চেষ্টা করুন।"
        
        elif response.status_code == 403:
            return "🔑 API key এ সমস্যা আছে। Admin কে জানান।"
        
        else:
            return f"❌ Error (Code: {response.status_code}). আবার চেষ্টা করুন।"
    
    except requests.Timeout:
        return "⏱️ Response পেতে সময় বেশি লাগছে। আবার চেষ্টা করুন।"
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return "❌ একটি সমস্যা হয়েছে। আবার চেষ্টা করুন।"

@app.route("/", methods=["POST"])
def telegram_webhook():
    """টেলিগ্রাম থেকে মেসেজ গ্রহণ করার ফাংশন"""
    try:
        data = request.get_json()
        print(f"Received webhook: {data}")
        
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            user_message = data["message"].get("text", "")
            
            if user_message:
                # Typing indicator দেখাও
                send_typing_action(chat_id)
                
                # বিশেষ commands handle করা
                if user_message.lower() == "/start":
                    welcome_msg = (
                        "👋 *হ্যালো! আমি Google Gemini AI চ্যাটবট।*\n\n"
                        "আমাকে বাংলা বা ইংরেজিতে যেকোনো প্রশ্ন করতে পারেন!\n\n"
                        "📝 *উদাহরণ:*\n"
                        "• AI কি?\n"
                        "• What is Python?\n"
                        "• একটা গল্প বলো\n"
                        "• Explain quantum physics\n"
                        "• বাংলাদেশ সম্পর্কে বলো\n\n"
                        "কমান্ড:\n"
                        "/start - শুরু করুন\n"
                        "/help - সাহায্য"
                    )
                    send_message(chat_id, welcome_msg)
                
                elif user_message.lower() == "/help":
                    help_msg = (
                        "ℹ️ *কীভাবে ব্যবহার করবেন:*\n\n"
                        "✅ বাংলা এবং ইংরেজি দুটোই supported\n"
                        "✅ যেকোনো প্রশ্ন করতে পারেন\n"
                        "✅ দ্রুত response পাবেন\n"
                        "✅ Code, story, explanation সব করতে পারি\n\n"
                        "*বিশেষ কমান্ড:*\n"
                        "/start - শুরু করুন\n"
                        "/help - এই help message\n\n"
                        "Powered by *Google Gemini AI* 🤖"
                    )
                    send_message(chat_id, help_msg)
                
                else:
                    # Gemini AI থেকে উত্তর নিন
                    ai_response = get_gemini_response(user_message)
                    
                    # টেলিগ্রামে পাঠান
                    send_message(chat_id, ai_response)
        
        return "OK", 200
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return "OK", 200

@app.route("/")
def home():
    """Bot চালু আছে কিনা চেক করার জন্য"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Bot</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                text-align: center;
                background: rgba(255,255,255,0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            h1 { margin: 0; font-size: 2.5em; }
            .status { 
                display: inline-block;
                background: #10b981;
                padding: 10px 20px;
                border-radius: 25px;
                margin-top: 20px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Telegram Bot</h1>
            <div class="status">✅ Online & Running</div>
            <p style="margin-top: 20px; opacity: 0.9;">Powered by Google Gemini AI</p>
        </div>
    </body>
    </html>
    """

@app.route("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "bot": "online",
        "ai": "Google Gemini",
        "version": "2.0"
    }, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Gemini Bot on port {port}")
    app.run(host="0.0.0.0", port=port)
