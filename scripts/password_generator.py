"""
Script to use AI LLM to generate "human-like" passwords for study
"""
import os
import re
import csv
import sys
import json
from google import genai
from config import API_KEY

# --- SETTINGS ---
TARGET_COUNT = 5000
CHUNK_SIZE = 25  # Number of personas to request per API call
OUTPUT_JSON = "personas.json"
OUTPUT_CSV = "credentials.csv"
SECTORS = ["Banking", "Healthcare", "Construction", "Education", "Retail", "Tech"]

client = genai.Client(api_key=API_KEY)

def validate_password(pw):
    """The Gatekeeper: 12+ chars and 3 of 4: Upper, Lower, Digit, Symbol."""
    if not pw or len(pw) < 12:
        return False
    classes = [
        re.search(r'[a-z]', pw),
        re.search(r'[A-Z]', pw),
        re.search(r'[0-9]', pw),
        re.search(r'[^a-zA-Z0-9]', pw)
    ]
    return sum(1 for c in classes if c) >= 3

def get_prompt(count, sector):
    """ generate a prompt with a seeded value """
    return f"""
    Generate {count} unique personas for a study on password habits in the {sector} sector.
    RESEARCH FOCUS: Credential Reuse.
    - personal_password: Raw human root (hobbies, slang, pet names).
    - work_password: A modification of that root (12+ chars, numbers, symbols).

    Return a JSON list of objects with these keys:
    name, occupation, personal_email, personal_password, work_lanid, work_password, behavior_tag
    """

def run_study():
    target_sector_override = sys.argv[1] if len(sys.argv) > 1 else None
    all_personas = []

    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, 'r') as f:
                all_personas = json.load(f)
        except:
            pass

    print(f"🚀 Target: {TARGET_COUNT} | Starting at: {len(all_personas)}")

    while len(all_personas) < TARGET_COUNT:
        # Determine sector for this chunk
        sector = target_sector_override if target_sector_override else SECTORS[len(all_personas) % len(SECTORS)]

        # Calculate how many to ask for (don't exceed CHUNK_SIZE or remaining target)
        request_count = min(CHUNK_SIZE, TARGET_COUNT - len(all_personas))

        try:
            # Using response_mime_type forces the model to stay in JSON mode
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=get_prompt(request_count, sector),
                config={'response_mime_type': 'application/json'}
            )

            batch_data = json.loads(response.text)

            # If the model returned a dict with a list inside, or just a list
            if isinstance(batch_data, dict):
                # Sometimes models wrap lists in a key; try to find it
                batch_data = next(iter(batch_data.values())) if isinstance(next(iter(batch_data.values())), list) else []

            valid_batch = [p for p in batch_data if validate_password(p.get('work_password', ''))]

            if not valid_batch:
                print(f"⚠️ Sector {sector}: 0 passed requirements. Retrying...")
                continue

            all_personas.extend(valid_batch)

            # Atomic-ish Save
            with open(OUTPUT_JSON, 'w') as f:
                json.dump(all_personas, f, indent=4)

            # CSV Append
            file_exists = os.path.isfile(OUTPUT_CSV)
            with open(OUTPUT_CSV, 'a', newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                if not file_exists:
                    writer.writerow(["user_id", "password"])
                for p in valid_batch:
                    writer.writerow([p['personal_email'], p['personal_password']])
                    writer.writerow([p['work_lanid'], p['work_password']])

            print(f"[✓] Sector: {sector:12} | Added: {len(valid_batch)} | Total: {len(all_personas)}")

        except Exception as e:
            print(f"❌ Error during generation: {e}")
            # Optional: break or sleep/retry
            break

if __name__ == "__main__":
    run_study()
