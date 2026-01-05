"""
generate "human-like" passwords for study
"""
import json
import csv
import re
import os
import sys
import time
from google import genai
from config import API_KEY

# --- SETTINGS ---
TARGET_COUNT = 5000
CHUNK_SIZE = 10 # if it gets large, LLM gets suck into all patternal of related data
OUTPUT_JSON = "personas.json"
OUTPUT_CSV = "credentials.csv"
SECTORS = ["Banking", "Healthcare", "Construction", "Education", "Retail", "Tech"]

# --- FEATURES ---
ENABLE_BLACKLIST = True
BLACKLIST = [
    "password", "12345678", "qwertyuiop", "password123", "password123!",
    "admin123", "welcome1", "welcome1!", "changeme", "sunshine",
    "football", "p@ssword", "123456789", "iloveyou", "monkey",
    "dragon", "letmein", "p@$$w0rd", "spring2026", "summer2026",
    "winter2026", "autumn2026", "password!", "admin!123", "adminadmin"
]

# --- REPORTING COUNTERS ---
stats = {
    "total_generated": 0,
    "rejected_complexity": 0,
    "rejected_blacklist": 0,
    "rejected_duplicate": 0,
    "accepted": 0
}

client = genai.Client(api_key=API_KEY)

def validate_password(pw):
    """Returns (is_valid, reason)"""
    if not pw or len(pw) < 12:
        return False, "complexity"

    classes = [
        re.search(r'[a-z]', pw), re.search(r'[A-Z]', pw),
        re.search(r'[0-9]', pw), re.search(r'[^a-zA-Z0-9]', pw)
    ]
    if sum(1 for c in classes if c) < 3:
        return False, "complexity"

    if ENABLE_BLACKLIST and pw.lower() in [b.lower() for b in BLACKLIST]:
        return False, "blacklist"

    return True, None


def get_prompt(count, sector):
    """ generate a prompt with a seeded value """
    return f"""
    Generate {count} unique personas for a study on password habits in the {sector} sector.
    RESEARCH FOCUS: Credential Reuse.
    - Diversity: Use a wide range of first and last names from different cultural backgrounds.
    - personal_password: Raw human root (hobbies, slang, pet names).
    - work_password: A modification of that root (12+ chars, numbers, symbols).

    Return a JSON list of objects with these keys:
    name, occupation, personal_email, personal_password, work_lanid, work_password, behavior_tag
    """

def run_study():
    """ create personas with passwords """
    target_sector_override = sys.argv[1] if len(sys.argv) > 1 else None
    all_personas = []
    seen_ids = set()

    # Load existing state
    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, 'r') as f:
                all_personas = json.load(f)
                stats["accepted"] = len(all_personas)
                for p in all_personas:
                    if p.get('personal_email'): seen_ids.add(p['personal_email'].lower())
                    if p.get('work_lanid'): seen_ids.add(p['work_lanid'].lower())
        except Exception as e:
            print(f"Note: Could not load existing JSON: {e}")

    print(f"🚀 Target: {TARGET_COUNT} | Blacklist: {'ON' if ENABLE_BLACKLIST else 'OFF'}")
    print(f"📊 Starting with {len(all_personas)} existing personas.")

    while len(all_personas) < TARGET_COUNT:
        sector = target_sector_override if target_sector_override else SECTORS[len(all_personas) % len(SECTORS)]
        request_count = min(CHUNK_SIZE, TARGET_COUNT - len(all_personas))

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=get_prompt(request_count, sector),
                config={'response_mime_type': 'application/json'}
            )

            batch_data = json.loads(response.text)
            if isinstance(batch_data, dict):
                batch_data = next(iter(batch_data.values())) if isinstance(next(iter(batch_data.values())), list) else []

            valid_batch = []
            for p in batch_data:
                stats["total_generated"] += 1

                # Deduplication Check
                p_email = p.get('personal_email', '').lower()
                w_id = p.get('work_lanid', '').lower()

                if not p_email or not w_id or p_email in seen_ids or w_id in seen_ids:
                    stats["rejected_duplicate"] += 1
                    continue

                # Validation Check
                is_valid, reason = validate_password(p.get('work_password', ''))

                if is_valid:
                    p['sector'] = sector
                    valid_batch.append(p)
                    seen_ids.add(p_email)
                    seen_ids.add(w_id)
                    stats["accepted"] += 1
                else:
                    if reason == "complexity": stats["rejected_complexity"] += 1
                    if reason == "blacklist": stats["rejected_blacklist"] += 1

            all_personas.extend(valid_batch)

            # --- PROGRESS REPORT ---
            total = stats["total_generated"] or 1
            print(f"\n--- Progress: {len(all_personas)}/{TARGET_COUNT} [{sector}] ---")
            print(f"  Complexity Rejections: {(stats['rejected_complexity']/total)*100:.1f}%")
            print(f"  Blacklist Rejections:  {(stats['rejected_blacklist']/total)*100:.1f}%")
            print(f"  Duplicate Rejections:  {(stats['rejected_duplicate']/total)*100:.1f}%")

            # Write JSON
            with open(OUTPUT_JSON, 'w') as f:
                json.dump(all_personas, f, indent=4)

            # Write/Append CSV
            file_is_empty = not os.path.exists(OUTPUT_CSV) or os.path.getsize(OUTPUT_CSV) == 0
            with open(OUTPUT_CSV, 'a', newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                if file_is_empty:
                    writer.writerow(["user_id", "password"])
                for p in valid_batch:
                    writer.writerow([p['personal_email'], p['personal_password']])
                    writer.writerow([p['work_lanid'], p['work_password']])

        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(2)
            continue

if __name__ == "__main__":
    run_study()
