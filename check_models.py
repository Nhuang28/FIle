import google.generativeai as genai
import os
from config import Config

# Load API Key from environment or config
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment variables.")
    # Try to verify if it's in Config but not loaded into env for this script context
    # In a real app run, flask loads config. But here we mimic it.
    pass

if not api_key:
    print("Please ensure GEMINI_API_KEY is set.")
    exit(1)

print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")

try:
    genai.configure(api_key=api_key)
    print("Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- Name: {m.name}")
            print(f"  Display Name: {m.display_name}")
            print(f"  Description: {m.description}")
            print("-" * 20)
except Exception as e:
    print(f"Error listing models: {e}")
