import os
import csv
import json
from google import genai
from config import API_KEY

# Setup the LLM
model = genai.Client(api_key=API_KEY)

def fetch_personas(count=10):
    prompt = f"""
    Generate {count} highly distinct fictional personas that reflext realistic, everyday human password behaviors.
    Each persona must include:
    - name (full name, do not use double quotes for nicknames)
    - occupation
    - personality_trait
    - personal_email (fictional free email)
    - personal_password (realistic habits: e.g., 'NameYear', 'Word123' or a phrase like 'ilovemycat')
    - work_lanid (Standard corporate ID: First inital + Last name, e.g., 'jdoe' or 'smithj')
    - work_password (12+ chars: must satisfy a corporate policy requiring at least one uppercase, one number, and one symbol, but should look like a person's quick-fix solution to a forced password change)

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
    data = fetch_personas()
    csv_file = "credentials.csv"
    file_is_new = not os.path.exists(csv_file)
    with open(csv_file, "a", newline="", encoding="utf-8") as cf:
        writer = csv.writer(cf, quoting=csv.QUOTE_ALL)
        if file_is_new:
            writer.writerow(["user", "password"])
        for p in data:
            writer.writerow([p.get("personal_email"), p.get("personal_password")])
            writer.writerow([p.get("work_lanid"), p.get("work_password")])
