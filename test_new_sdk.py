import os
import traceback
try:
    from google import genai
    print(dir(genai))
except Exception as e:
    traceback.print_exc()
