import firebase_admin
from firebase_admin import credentials, firestore
from google import genai
import os
from datetime import datetime, timedelta

def send_weekly_retrospectives():
    if not firebase_admin._apps:
        cred_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if cred_json:
            import json
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app()
            
    db = firestore.client()
    users = db.collection('users').stream()
    
    one_week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
    
    for user_doc in users:
        user_data = user_doc.to_dict()
        user_id = user_doc.id
        email = user_data.get("email")
        if not email: continue
        
        # Gather completed tasks in the last 7 days
        tasks = db.collection('users').document(user_id).collection('tasks').where("completed_at", ">=", one_week_ago).stream()
        task_list = [t.to_dict().get('title') for t in tasks]
        
        if not task_list: continue
        
        prompt = f"""
        You are the AI Productivity Coach for {user_data.get('displayName', 'this user')}.
        Here are the tasks they successfully completed this week: {', '.join(task_list)}
        
        Write a short, engaging, slightly aggressive but encouraging 3-paragraph email summarizing their week.
        Do not use markdown formatting.
        """
        
        try:
            resp = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
            email_body = resp.text
            
            # Here you would integrate SendGrid / Mailgun
            # e.g., requests.post("https://api.sendgrid.com/v3/mail/send", ...)
            print(f"--- EMAIL TO {email} ---\n{email_body}\n----------------------")
        except Exception as e:
            print(f"Failed to generate retro for {email}: {e}")

if __name__ == "__main__":
    send_weekly_retrospectives()
