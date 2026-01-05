from google import genai
import json
import os
from config import API_KEY

# Setup the LLM
model = genai.Client(api_key=API_KEY)

def fetch_personas(count=10):
    prompt = f"""
    Generate a list of {count} diverse fictional user personas for a behavioral security study.
    Each persona must include:
    - name (full name, do not use double quotes for nicknames)
    - occupation
    - personality_trait
    - personal_password (realistic habits: e.g., 'NameYear', 'Word123' or a phrase like 'ilovemycat')
    - work_password (a complex, persona-driven password: 12+ chars, symbols)

    Return ONLY raw JSON.
    """

    print(f"[*] Requesting {count} personas from Gemini...")
    response = model.models.generate_content(model="gemini-2.0-flash", contents=prompt)

    # Clean the response to ensure it's valid JSON
    raw_text = response.text.strip()
    if "```json" in raw_text:
        raw_text = raw_text.split("```json")[1].split("```")[0].strip()

    try:
        data = json.loads(raw_text)
        with open("personas.json", "w") as f:
            json.dump(data, f, indent=4)
        print("[+] Success! Personas saved to personas.json")
        return data
    except Exception as e:
        print(f"[-] Error parsing JSON: {e}")
        print("Raw response for debugging:", raw_text)
        return None

if __name__ == "__main__":
    fetch_personas()
