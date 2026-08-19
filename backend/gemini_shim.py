import os
import json
from google import genai
from google.genai import types

def chat(model, messages, **kwargs):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
    
    system_instruction = ""
    contents = []
    
    for msg in messages:
        if msg['role'] == 'system':
            system_instruction += msg['content'] + "\n"
        else:
            role = "user" if msg['role'] == 'user' else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg['content'])]))
            
    config = types.GenerateContentConfig()
    if system_instruction:
        config.system_instruction = system_instruction
        
    if kwargs.get('format') == 'json':
        config.response_mime_type = 'application/json'

    resp = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
    
    text = resp.text
    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()
        
    return {"message": {"content": text}}

def generate(model, prompt, images=None, **kwargs):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
    
    parts = [types.Part.from_text(text=prompt)]
    if images:
        for img in images:
            # Assuming images are base64 strings if passed this way, but genai might need raw bytes
            # The shim previously just passed dict with mime_type and data. Let's replicate or adapt.
            import base64
            # if img is a b64 string
            img_bytes = base64.b64decode(img)
            parts.append(types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg'))
            
    resp = client.models.generate_content(
        model=model,
        contents=parts
    )
    
    text = resp.text
    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()
    return {"response": text}
