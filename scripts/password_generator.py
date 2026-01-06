""" generate "human-like" passwords for study """
import os
import csv
import sys
import json
import time
import uuid
import string
from collections import Counter
from google import genai
from config import API_KEY

# --- SETTINGS ---
TARGET_COUNT = 2500
CHUNK_SIZE = 15
OUTPUT_JSON = "personas.json"
OUTPUT_CSV = "credentials.csv"
SUMMARY_FILE = "data_summary.txt"
SECTORS = ["Banking", "Healthcare", "Construction", "Education", "Retail", "Tech"]

# --- FEATURES ---
ENABLE_BLOCKLIST = True
BLOCKLIST = [
    "password", "12345678", "qwertyuiop", "password123", "password123!",
    "admin123", "welcome1", "welcome1!", "changeme", "sunshine",
    "football", "p@ssword", "123456789", "iloveyou", "monkey",
    "dragon", "letmein", "p@$$w0rd", "spring2026", "summer2026",
    "winter2026", "autumn2026", "password!", "admin!123", "adminadmin"
]

VALID_SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

# --- REPORTING COUNTERS ---
stats = {
    "total_generated": 0,
    "rejected_complexity": 0,
    "rejected_blocklist": 0,
    "rejected_pattern": 0,  # Renamed from forbidden
    "rejected_duplicate_persona": 0,
    "accepted": 0
}

personal_pw_registry = Counter()
work_pw_registry = Counter()

client = genai.Client(api_key=API_KEY)

def validate_password(pw, check_complexity=True):
    """
    Pattern-based character filter.
    Rejects: Emojis, Unicode, and Spaces (since space is not in VALID_SYMBOLS).
    """
    if not pw:
        return False, "empty"

    # Pattern check (The filter for characters outside your allow-list)
    all_allowed = string.ascii_letters + string.digits + VALID_SYMBOLS
    if any(c not in all_allowed for c in pw):
        return False, "pattern"

    if check_complexity:
        if len(pw) < 12:
            return False, "complexity"
        has_low = any(c in string.ascii_lowercase for c in pw)
        has_up  = any(c in string.ascii_uppercase for c in pw)
        has_num = any(c in string.digits for c in pw)
        has_sym = any(c in VALID_SYMBOLS for c in pw)

        if sum([has_low, has_up, has_num, has_sym]) < 3:
            return False, "complexity"

        if ENABLE_BLOCKLIST and pw.lower() in [b.lower() for b in BLOCKLIST]:
            return False, "blocklist"

    return True, None

def get_prompt(count, sector):
    batch_seed = uuid.uuid4().hex[:8]
    return f"""
    Generate {count} unique personas for a study on password habits in the {sector} sector.
    Batch Seed: {batch_seed}
    - Diversity: Global mix of names and backgrounds.
    - personal_password: Raw human root (hobbies, slang, pet names). Single word, no spaces/emojis.
    - work_password: A modification of that root (12+ chars, numbers, symbols). No spaces/emojis.
    Return a JSON list: name, occupation, personal_email, personal_password, work_lanid, work_password, behavior_tag
    """

def write_summary():
    with open(SUMMARY_FILE, "w") as f:
        f.write(f"=== PERSONA STUDY DATA SUMMARY | {time.ctime()} ===\n")
        f.write(f"Total Accepted: {stats['accepted']} / {TARGET_COUNT}\n")
        f.write(f"Total API Attempts: {stats['total_generated']}\n")
        f.write(f"Rejection - Duplicate:  {stats['rejected_duplicate_persona']}\n")
        f.write(f"Rejection - Pattern:    {stats['rejected_pattern']} (Emoji/Spaces/Unallowed Symbols)\n")
        f.write(f"Rejection - Complexity: {stats['rejected_complexity']}\n")
        f.write(f"Rejection - Blocklist:  {stats['rejected_blocklist']}\n\n")

        f.write("--- TOP 10 PERSONAL ROOTS ---\n")
        for pw, count in personal_pw_registry.most_common(10):
            f.write(f"{pw}: {count}\n")

        f.write("\n--- TOP 10 WORK PASSWORDS ---\n")
        for pw, count in work_pw_registry.most_common(10):
            f.write(f"{pw}: {count}\n")

def run_study():
    target_sector_override = sys.argv[1] if len(sys.argv) > 1 else None
    all_personas = []
    seen_ids = set()

    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, 'r') as f:
                all_personas = json.load(f)
                stats["accepted"] = len(all_personas)
                for p in all_personas:
                    seen_ids.add(p['personal_email'].lower())
                    seen_ids.add(p['work_lanid'].lower())
                    personal_pw_registry[p['personal_password']] += 1
                    work_pw_registry[p['work_password']] += 1
        except Exception: pass

    while len(all_personas) < TARGET_COUNT:
        sector = target_sector_override if target_sector_override else SECTORS[len(all_personas) % len(SECTORS)]
        request_count = min(CHUNK_SIZE, TARGET_COUNT - len(all_personas))

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=get_prompt(request_count, sector),
                config={'response_mime_type': 'application/json', 'temperature': 1.4}
            )
            batch_data = json.loads(response.text)
            if isinstance(batch_data, dict):
                batch_data = next(iter(batch_data.values()))

            valid_batch = []
            for p in batch_data:
                stats["total_generated"] += 1
                p_email = p.get('personal_email', '').lower()
                w_id = p.get('work_lanid', '').lower()

                if not p_email or p_email in seen_ids or w_id in seen_ids:
                    stats["rejected_duplicate_persona"] += 1
                    continue

                # Re-roll check: Validate Personal (Pattern only) and Work (Pattern + Complexity)
                is_p_v, p_r = validate_password(p.get('personal_password', ''), check_complexity=False)
                is_w_v, w_r = validate_password(p.get('work_password', ''), check_complexity=True)

                if is_p_v and is_w_v:
                    p['sector'] = sector
                    valid_batch.append(p)
                    seen_ids.add(p_email)
                    seen_ids.add(w_id)
                    stats["accepted"] += 1
                    personal_pw_registry[p['personal_password']] += 1
                    work_pw_registry[p['work_password']] += 1
                else:
                    # Log the rejection reason (Personal failures prioritized in reporting)
                    reason = p_r if not is_p_v else w_r
                    if reason == "pattern":
                        stats["rejected_pattern"] += 1
                    elif reason == "complexity":
                        stats["rejected_complexity"] += 1
                    elif reason == "blocklist":
                        stats["rejected_blocklist"] += 1

            all_personas.extend(valid_batch)
            with open(OUTPUT_JSON, 'w') as f: json.dump(all_personas, f, indent=4)

            file_exists = os.path.exists(OUTPUT_CSV) and os.path.getsize(OUTPUT_CSV) > 0
            with open(OUTPUT_CSV, 'a', newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                if not file_exists:
                    writer.writerow(["user_id", "password"])
                for p in valid_batch:
                    writer.writerow([p['personal_email'], p['personal_password']])
                    writer.writerow([p['work_lanid'], p['work_password']])

            write_summary()

            # Enhanced Terminal Reporting
            print(f"\n--- Progress: {len(all_personas)}/{TARGET_COUNT} Sector: [{sector}] ---")
            print(f"  [REJECTIONS] Pattern: {stats['rejected_pattern']} | Complex: {stats['rejected_complexity']} | Block: {stats['rejected_blocklist']}")
            print(f"  [IDENTITY]  Duplicates Found: {stats['rejected_duplicate_persona']}")
            print(f"  [REUSE]     Personal Roots: {len(personal_pw_registry)}/{len(all_personas)} Unique")
            print(f"  [COLLISION] Work Passwords: {len(work_pw_registry)}/{len(all_personas)} Unique")

        except Exception as e:
            print(f"❌ API/Parse Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    run_study()
