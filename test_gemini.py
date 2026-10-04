from dotenv import load_dotenv
import os

load_dotenv()

key = os.getenv("GEMINI_API_KEY")

print("\n==============================")
print("GEMINI KEY CHECK")
print("==============================")

if not key:
    print("❌ GEMINI_API_KEY was NOT found.")
else:
    print("✅ GEMINI_API_KEY was found.")
    print("Key length:", len(key))
    print("Starts with:", key[:6])
    print("Ends with:", key[-4:])

print("==============================\n")