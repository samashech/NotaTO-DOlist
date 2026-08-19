import os
import traceback

print("Trying with google.generativeai")
try:
    import google.generativeai as genai
    genai.configure(api_key="AQ.testkey")
    m = genai.GenerativeModel('gemini-2.5-flash')
    resp = m.generate_content("hello")
    print(resp.text)
except Exception as e:
    print(f"genai error: {e}")
    traceback.print_exc()

