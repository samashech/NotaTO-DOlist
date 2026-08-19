import google.generativeai as genai
import os
import json

class MockMessage:
    def __init__(self, content):
        self.content = content

def chat(model, messages, **kwargs):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
    system_instruction = ""
    prompt = ""
    for msg in messages:
        if msg['role'] == 'system':
            system_instruction += msg['content'] + "\n"
        else:
            prompt += f"{msg['role'].upper()}: {msg['content']}\n\n"
            
    m = genai.GenerativeModel(model, system_instruction=system_instruction if system_instruction else None)
    resp = m.generate_content(prompt)
    
    text = resp.text
    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()
        
    return {"message": {"content": text}}

def generate(model, prompt, images=None, **kwargs):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
    contents = [prompt]
    if images:
        for img in images:
            contents.append({
                "mime_type": "image/jpeg",
                "data": img
            })
    
    m = genai.GenerativeModel(model)
    resp = m.generate_content(contents)
    text = resp.text
    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()
    return {"response": text}
