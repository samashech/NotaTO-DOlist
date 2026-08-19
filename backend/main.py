import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime

from fastapi import Depends, FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

# Setup structured logging
logger = logging.getLogger("ai_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)

def log_ai_call(endpoint: str, user_id: str, latency: float, success: bool, error: str = "", tokens: int = 0):
    log_data = {
        "event": "ai_request",
        "request_id": str(uuid.uuid4()),
        "user_id_hash": hashlib.sha256(user_id.encode()).hexdigest() if user_id else "anonymous",
        "endpoint": endpoint,
        "latency_ms": round(latency * 1000, 2),
        "success": success,
        "error": error,
        "tokens": tokens
    }
    logger.info(json.dumps(log_data))

def call_gemini_structured(prompt: str, schema_model, default_fallback: dict, endpoint_name: str, user_id: str = ""):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
    schema_schema = schema_model.schema_json()
    
    config = types.GenerateContentConfig(
        response_mime_type='application/json',
        system_instruction=f'You are a precise JSON-generating assistant. Output exactly matching this schema: {schema_schema}'
    )
    
    start_time = time.time()
    try:
        resp = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=config
        )
        latency = time.time() - start_time
        tokens = resp.usage_metadata.total_token_count if hasattr(resp, "usage_metadata") else 0
        
        text = resp.text
        if text.startswith("```json"): text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"): text = text.replace("```", "").strip()
        
        # Validation
        try:
            validated = schema_model.parse_raw(text)
            log_ai_call(endpoint_name, user_id, latency, True, tokens=tokens)
            return validated.dict()
        except ValidationError:
            # Retry once
            retry_prompt = f"Your previous output was invalid. STRICTLY output valid JSON matching this schema:\n{schema_schema}\n\nOriginal Request:\n{prompt}"
            retry_start = time.time()
            resp2 = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=retry_prompt,
                config=config
            )
            retry_latency = time.time() - retry_start
            retry_tokens = resp2.usage_metadata.total_token_count if hasattr(resp2, "usage_metadata") else 0
            
            text2 = resp2.text
            if text2.startswith("```json"): text2 = text2.replace("```json", "").replace("```", "").strip()
            elif text2.startswith("```"): text2 = text2.replace("```", "").strip()
            
            validated2 = schema_model.parse_raw(text2)
            log_ai_call(endpoint_name, user_id, latency + retry_latency, True, tokens=tokens + retry_tokens)
            return validated2.dict()
            
    except Exception as e:
        latency = time.time() - start_time
        log_ai_call(endpoint_name, user_id, latency, False, error=str(e))
        return default_fallback


class OnboardingTask(BaseModel):
    title: str
    description: str
    estimated_hours: float
    priority: str

class OnboardingResponse(BaseModel):
    tasks: list[OnboardingTask]

class RiskResponse(BaseModel):
    risk_score: int
    recommendation: str
    breakdown: list[str]

import sentry_sdk

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN", ""),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = FastAPI(title="Deadline Guardian AI API")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with frontend URL
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"])

class Task(BaseModel):
    id: str
    title: str
    description: str | None = None
    due_date: str
    estimated_hours: float
    status: str = "pending"
    priority: str = "medium"
    blocked_sites: list[str] = []
    created_at: str | None = None
    completed_at: str | None = None

class Habit(BaseModel):
    id: str
    title: str
    streak: int = 0
    completed_today: bool = False
    tracked_domains: list[str] = []
    requires_proof: bool = False


import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin
if not firebase_admin._apps:
    cred_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if cred_json:
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    else:
        try:
            firebase_admin.initialize_app()
        except Exception as e:
            print(f"Warning: Firebase init failed. {e}")

try:
    db = firestore.client()
except Exception as e:
    db = None
    print(f"Warning: Firestore client failed to initialize. {e}")

ACTIVE_USER_ID = "default"

def get_user_id(x_user_id: str | None = Header(None)):
    global ACTIVE_USER_ID
    if x_user_id:
        ACTIVE_USER_ID = x_user_id
    return ACTIVE_USER_ID


@app.get("/")
def read_root():
    return {"message": "Welcome to the Deadline Guardian AI API"}

@app.get("/api/tasks")
def get_tasks(user_id: str = Depends(get_user_id)):
    if not db: return []
    now = datetime.now()
    tasks_ref = db.collection('users').document(user_id).collection('tasks')
    docs = tasks_ref.get()
    
    valid_tasks = []
    for doc in docs:
        t = doc.to_dict()
        if t.get("status") == "completed" and t.get("completed_at"):
            try:
                completed_date = datetime.fromisoformat(t["completed_at"])
                if (now - completed_date).days > 7:
                    tasks_ref.document(doc.id).delete()
                    continue
            except Exception:
                pass
        valid_tasks.append(t)
    return valid_tasks

@app.post("/api/tasks", response_model=Task)
def create_task(task: Task, user_id: str = Depends(get_user_id)):
    new_task = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date,
        "estimated_hours": task.estimated_hours,
        "status": task.status,
        "priority": task.priority,
        "blocked_sites": task.blocked_sites,
        "created_at": task.created_at or datetime.now().isoformat(),
        "completed_at": None
    }
    if db:
        db.collection('users').document(user_id).collection('tasks').document(task.id).set(new_task)
    return new_task

@app.put("/api/tasks/{task_id}")
def update_task_status(task_id: str, payload: dict, user_id: str = Depends(get_user_id)):
    if not db: return {"error": "db not initialized"}
    doc_ref = db.collection('users').document(user_id).collection('tasks').document(task_id)
    doc = doc_ref.get()
    if not doc.exists: return {"error": "not found"}
    
    t = doc.to_dict()
    old_status = t.get("status")
    
    updates = {}
    if "status" in payload: updates["status"] = payload["status"]
    if payload.get("status") == "completed" and old_status != "completed":
        updates["completed_at"] = datetime.now().isoformat()
    if "due_date" in payload: updates["due_date"] = payload["due_date"]
    if "estimated_hours" in payload: updates["estimated_hours"] = payload["estimated_hours"]
    if "title" in payload: updates["title"] = payload["title"]
    if "priority" in payload: updates["priority"] = payload["priority"]
    if "blocked_sites" in payload: updates["blocked_sites"] = payload["blocked_sites"]
    
    doc_ref.update(updates)
    t.update(updates)
    
    # Phase 3: AI Evaluation Layer - Update Judge Verdicts
    if payload.get("status") in ["completed", "failed"] and old_status != payload.get("status"):
        try:
            preds = db.collection('risk_predictions').where('task_id', '==', task_id).stream()
            for p in preds:
                p.reference.update({"actual_outcome": payload.get("status")})
        except Exception as e:
            print(f"Failed to update risk prediction outcome: {e}")
            
    return t

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str, user_id: str = Depends(get_user_id)):
    if db:
        db.collection('users').document(user_id).collection('tasks').document(task_id).delete()
    return {"status": "ok"}



class UsagePayload(BaseModel):
    domain: str
    seconds: int

@app.post("/api/usage")
def report_usage(payload: UsagePayload, user_id: str = Depends(get_user_id)):
    if not db: return {"status": "ok"}
    doc_ref = db.collection('users').document(user_id).collection('usage').document(payload.domain.replace('/', '_'))
    doc = doc_ref.get()
    if doc.exists:
        doc_ref.update({"seconds": firestore.Increment(payload.seconds)})
    else:
        doc_ref.set({"domain": payload.domain, "seconds": payload.seconds})
    return {"status": "ok"}

@app.get("/api/usage")
def get_usage(user_id: str = Depends(get_user_id)):
    if not db: return {}
    docs = db.collection('users').document(user_id).collection('usage').get()
    usage = {}
    for doc in docs:
        data = doc.to_dict()
        usage[data.get('domain', doc.id)] = data.get('seconds', 0)
    return usage

@app.get("/api/habits")
def get_habits(user_id: str = Depends(get_user_id)):
    if not db: return []
    docs = db.collection('users').document(user_id).collection('habits').get()
    return [doc.to_dict() for doc in docs]

@app.post("/api/habits")
def create_habit(habit: Habit, user_id: str = Depends(get_user_id)):
    new_h = habit.dict()
    if db:
        db.collection('users').document(user_id).collection('habits').document(habit.id).set(new_h)
    return new_h

@app.put("/api/habits/{habit_id}/toggle")
def toggle_habit(habit_id: str, user_id: str = Depends(get_user_id)):
    if not db: return {"error": "db not initialized"}
    doc_ref = db.collection('users').document(user_id).collection('habits').document(habit_id)
    doc = doc_ref.get()
    if not doc.exists: return {"error": "not found"}
    
    h = doc.to_dict()
    h["completed_today"] = not h.get("completed_today", False)
    if h["completed_today"]:
        h["streak"] = h.get("streak", 0) + 1
    else:
        h["streak"] = max(0, h.get("streak", 0) - 1)
        
    doc_ref.update({"completed_today": h["completed_today"], "streak": h["streak"]})
    return h

@app.put("/api/habits/{habit_id}")
def update_habit(habit_id: str, payload: dict, user_id: str = Depends(get_user_id)):
    if not db: return {"error": "db not initialized"}
    doc_ref = db.collection('users').document(user_id).collection('habits').document(habit_id)
    doc = doc_ref.get()
    if not doc.exists: return {"error": "not found"}
    
    if "title" in payload:
        doc_ref.update({"title": payload["title"]})
        h = doc.to_dict()
        h["title"] = payload["title"]
        return h
    return doc.to_dict()

@app.delete("/api/habits/{habit_id}")
def delete_habit(habit_id: str, user_id: str = Depends(get_user_id)):
    if db:
        db.collection('users').document(user_id).collection('habits').document(habit_id).delete()
    return {"status": "deleted"}

class VerifyPayload(BaseModel):
    image_base64: str

@app.post("/api/habits/{habit_id}/verify")
def verify_habit(habit_id: str, payload: VerifyPayload, user_id: str = Depends(get_user_id)):
    target_habit = None
    doc_ref = None
    if db:
        doc_ref = db.collection('users').document(user_id).collection('habits').document(habit_id)
        doc = doc_ref.get()
        if doc.exists: target_habit = doc.to_dict()
    
    if not target_habit:
        return {"error": "not found"}

    b64_data = payload.image_base64
    if "base64," in b64_data:
        b64_data = b64_data.split("base64,")[1]

    try:
        # Step 1: The "Eyes" (Gemini describes the image)
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
        import base64
        img_bytes = base64.b64decode(b64_data)
        vision_resp = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg'),
                types.Part.from_text(text="Describe exactly what is happening in this image in detail.")
            ]
        )
        image_description = vision_resp.text.strip()
        
        # Step 2: The "Judge" (Gemini evaluates the description)
        judge_prompt = f"""
        You are a strict AI judge. The user is trying to prove they completed the habit: "{target_habit['title']}".
        Here is what the camera sees: {image_description}
        
        Did the user complete the habit based on this description? 
        Answer strictly with the word YES or NO, followed by a one-sentence sassy explanation.
        """
        judge_resp = client.models.generate_content(model='gemini-3.5-flash', contents=judge_prompt)
        resp_text = judge_resp.text.strip()
        
        if resp_text.upper().startswith("YES"):
            result = {"verified": True, "sassy_reason": resp_text}
        else:
            result = {"verified": False, "sassy_reason": resp_text}
            
        if result.get("verified"):
            target_habit["completed_today"] = True
            target_habit["streak"] = target_habit.get("streak", 0) + 1
            if db and doc_ref:
                doc_ref.update({"completed_today": True, "streak": target_habit["streak"]})
        return result
    except Exception as e:
        return {"verified": False, "sassy_reason": f"AI Verification failed: {e!s}"}

class OnboardingRequest(BaseModel):
    user_mission: str

@app.post("/api/onboarding_generate")
def onboarding_generate(req: OnboardingRequest, user_id: str = Header(default="anonymous")):
    prompt = f"""
    The user wants to achieve this goal: {req.mission_statement}
    Break this down into 3-5 immediate, actionable tasks.
    Return JSON.
    """
    fallback = {"tasks": []}
    resp = call_gemini_structured(prompt, OnboardingResponse, fallback, "onboarding_generate", user_id)
    return {"tasks_json": json.dumps(resp["tasks"])}



@app.post("/api/analyze_risk")
def analyze_risk(task: Task, user_id: str = Header(default="anonymous")):
    PROMPT_VERSION = "v1.0"
    prompt = f"""
    You are an AI Productivity Coach. Analyze the following task and predict the risk of missing the deadline.
    
    Task: {task.title}
    Description: {task.description or 'No description provided'}
    Estimated Hours to Complete: {task.estimated_hours}
    Due Date: {task.due_date}
    
    Calculate a 'risk_score' (0-100) indicating the probability of failing to complete the task on time.
    Provide a 'recommendation' on what the user should do immediately.
    Break the task down into a 'breakdown' array of 3-5 smaller actionable steps.
    """
    
    fallback = {
        "risk_score": 50,
        "recommendation": "Unable to calculate risk. Please start working immediately.",
        "breakdown": ["Open your tools", "Begin step one", "Maintain focus"]
    }
    
    resp = call_gemini_structured(prompt, RiskResponse, fallback, "analyze_risk", user_id)
    
    # Log prediction to Firestore
    if db and user_id != "anonymous":
        try:
            db.collection('risk_predictions').add({
                "user_id": user_id,
                "task_id": task.id,
                "task_title": task.title,
                "prompt_version": PROMPT_VERSION,
                "predicted_risk_score": resp["risk_score"],
                "recommendation": resp["recommendation"],
                "timestamp": datetime.now().isoformat(),
                "actual_outcome": None # Will be updated when task is completed or failed
            })
        except Exception as e:
            print(f"Failed to log risk prediction: {e}")
            
    return resp



class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    tasks_context: str

@app.post("/api/chat")
def chat_with_ai(req: ChatRequest):
    system_prompt = f"""
    You are an aggressive but supportive AI Execution Coach.
    You have direct access to the user's task list: {req.tasks_context}
    
    Answer the user's questions based on their tasks. If they ask what to do, prioritize tasks with high risk scores.
    Be concise, direct, and actionable.
    
    CRITICAL FORMATTING RULE: ALWAYS respond using clear bullet points. Every single point must be on a new line. Never use long paragraphs.
    """
    
    # Prepend system prompt to the messages
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
        contents = []
        for msg in req.messages:
            role = "user" if msg.role == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))
        
        resp = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_prompt)
        )
        return {"reply": resp.text}
    except Exception as e:
        err_msg = str(e)
        if not os.environ.get("GEMINI_API_KEY"): err_msg = "API Key is empty!"
        return {"reply": f"Gemini Error: {err_msg}"}

class PlannerChatRequest(BaseModel):
    messages: list[ChatMessage]

@app.post("/api/planner_chat")
def planner_chat(req: PlannerChatRequest):
    current_time = datetime.now().isoformat()
    system_prompt = f"""
    You are an AI Task Planner. Your goal is to help the user create a highly specific task for their execution dashboard.
    The current date and time is: {current_time}.
    
    You need to collect 5 details from the user:
    1. Title
    2. Estimated Hours
    3. Priority level
    4. Due Date
    5. Blocked Sites
    
    CRITICAL RULES:
    - If the user provides a natural language due date (e.g., "tomorrow at 5pm"), you MUST accept it. DO NOT ask them to format it as an ISO string. You will do the conversion yourself at the end.
    - If the user says "1 hour", accept it. DO NOT ask them to format it as a float.
    - If you are missing any of the 5 pieces of information, reply ONLY with a concise bulleted list of what you still need. DO NOT ask for exact formats.
      Example:
      "Got it. I still need:
      - Estimated duration
      - Any websites to block"
    - NEVER mention the word "JSON", "ISO format", or "float" to the user.
    
    IMPORTANT TRIGGER: ONCE you have all 5 pieces of information (even in casual language), you MUST STOP conversing and output ONLY a JSON block, surrounded by triple backticks, where YOU format the data correctly:
    ```json
    {{
      "action": "CREATE_TASK",
      "task": {{
        "title": "Study Biology",
        "estimated_hours": 2.5,
        "priority": "high",
        "due_date": "2026-06-25T15:00:00",
        "blocked_sites": ["youtube.com", "instagram.com"]
      }}
    }}
    ```
    Do not add ANY conversational text before or after the JSON block. Output ONLY the JSON block.
    """
    
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
        contents = []
        for msg in req.messages:
            role = "user" if msg.role == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))
        
        resp = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_prompt)
        )
        return {"reply": resp.text}
    except Exception as e:
        err_msg = str(e)
        if not os.environ.get("GEMINI_API_KEY"): err_msg = "API Key is empty!"
        return {"reply": f"Gemini Error: {err_msg}"}

@app.post("/api/interrogation_chat")
def interrogation_chat(req: PlannerChatRequest):
    current_time = datetime.now().isoformat()
    system_prompt = f"""
    You are an aggressive, strict AI Accountability Coach. The user has FAILED to meet their deadline.
    The current date and time is: {current_time}.
    
    Your goal is to:
    1. Interrogate them on WHY they failed.
    2. Force them to commit to a NEW deadline (Date/Time) and NEW estimated hours to finish the task.
    
    CRITICAL RULES:
    - Keep responses short, direct, and slightly scolding but constructive.
    - Accept any natural language date for the new deadline (e.g. "tomorrow 5pm") and silently convert it to ISO format.
    - NEVER mention the word "JSON", "code", or "compiling".
    
    IMPORTANT TRIGGER: ONCE the user has explained themselves AND provided a new deadline and estimated hours, you MUST output ONLY a JSON block like this, surrounded by triple backticks:
    ```json
    {{
      "action": "RESCHEDULE_TASK",
      "task": {{
        "due_date": "2026-06-25T15:00:00",
        "estimated_hours": 2.5
      }}
    }}
    ```
    Do not add ANY conversational text before or after the JSON block. Output ONLY the JSON block.
    """
    
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
        contents = []
        for msg in req.messages:
            role = "user" if msg.role == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))
        
        resp = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_prompt)
        )
        return {"reply": resp.text}
    except Exception as e:
        err_msg = str(e)
        if not os.environ.get("GEMINI_API_KEY"): err_msg = "API Key is empty!"
        return {"reply": f"Gemini Error: {err_msg}"}

class UploadSchedulePayload(BaseModel):
    image_base64: str

@app.post("/api/upload_schedule")
def upload_schedule(payload: UploadSchedulePayload, user_id: str = Depends(get_user_id)):
    b64_data = payload.image_base64
    is_pdf = "application/pdf" in b64_data
    if "base64," in b64_data:
        b64_data = b64_data.split("base64,")[1]
    
    try:
        schedule_text = ""
        import base64
        import io
        if is_pdf:
            from pypdf import PdfReader
            pdf_bytes = base64.b64decode(b64_data)
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                text = page.extract_text()
                if text: schedule_text += text + "\\n"
        else:
            # Step 1: Gemini OCR
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
            img_bytes = base64.b64decode(b64_data)
            vision_resp = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg'),
                    types.Part.from_text(text="Read this entire schedule/timetable and extract all the text, events, and dates exactly as they appear.")
                ]
            )
            schedule_text = vision_resp.text.strip()
        
        # Step 2: Gemini logic
        current_time = datetime.now().isoformat()
        prompt = f"""
        You are a strict, highly intelligent AI Task Planner. The user uploaded a schedule.
        Here is the text extracted from the schedule: 
        {schedule_text}
        
        The current date and time is: {current_time}.
        
        Your job is to reverse-engineer this schedule and generate a list of preparation tasks leading up to the events. 
        """
        
        class PrepTask(BaseModel):
            title: str
            estimated_hours: float
            priority: str
            due_date: str
            blocked_sites: list[str]
            
        class ScheduleResponse(BaseModel):
            tasks: list[PrepTask]
        
        fallback = {"tasks": []}
        resp = call_gemini_structured(prompt, ScheduleResponse, fallback, "upload_schedule", user_id)
        
        created_tasks = []
        for td in resp["tasks"]:
            task_id = str(uuid.uuid4())[:8]
            new_task = {
                "id": task_id,
                "title": td.get("title", "Prep Task"),
                "description": None,
                "due_date": td.get("due_date", current_time),
                "estimated_hours": float(td.get("estimated_hours", 1.0)),
                "status": "pending",
                "priority": td.get("priority", "high"),
                "blocked_sites": td.get("blocked_sites", ["youtube.com"]),
                "created_at": current_time,
                "completed_at": None
            }
            if db:
                db.collection('users').document(user_id).collection('tasks').document(task_id).set(new_task)
            created_tasks.append(new_task)
            
        return {"status": "success", "tasks_created": len(created_tasks), "tasks": created_tasks}
    except Exception as e:
        print(f"Schedule Parse Error: {e}")
        return {"error": str(e)}



@app.get("/api/admin/accuracy")
def admin_accuracy():
    if not db: return {"error": "db not initialized"}
    try:
        preds = db.collection('risk_predictions').stream()
        total_predictions = 0
        completed = 0
        failed = 0
        avg_risk_score = 0
        
        for p in preds:
            data = p.to_dict()
            total_predictions += 1
            avg_risk_score += data.get("predicted_risk_score", 0)
            if data.get("actual_outcome") == "completed":
                completed += 1
            elif data.get("actual_outcome") == "failed":
                failed += 1
                
        if total_predictions > 0:
            avg_risk_score /= total_predictions
            
        return {
            "total_predictions": total_predictions,
            "average_risk_score": avg_risk_score,
            "outcomes": {
                "completed": completed,
                "failed": failed,
                "pending": total_predictions - (completed + failed)
            }
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
