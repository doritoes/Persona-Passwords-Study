"" generate "human-like" passwords for study - Hardened ASCII Version """
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

# --- RIGID CHARACTER CONSTRAINTS ---
VALID_SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
# Only allows A-Z, a-z, 0-9, and specific symbols. Strictly No Emojis/Unicode.
ALLOWED_CHARS = set(string.ascii_letters + string.digits + VALID_SYMBOLS)

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
    "rejected_forbidden": 0,
    "rejected_duplicate_persona": 0,
    "accepted": 0
}

personal_pw_registry = Counter()
work_pw_registry = Counter()

client = genai.Client(api_key=API_KEY)

def validate_password(pw):
    """ Strict white-list validation to prevent emojis and non-standard input """
    if not pw or len(pw) < 12:
        return False, "complexity"

    # KILL-SWITCH: If any char is not in the allowed ASCII set, reject immediately
    if not all(c in ALLOWED_CHARS for c in pw):
        return False, "forbidden"

    has_low = any(c in string.ascii_lowercase for c in pw)
    has_up  = any(c in string.ascii_uppercase for c in pw)
    has_num = any(c in string.digits for c in pw)
    has_sym = any(c in VALID_SYMBOLS for c in pw)

    if sum([has_low, has_up, has_num, has_sym]) < 3:
        return False, "complexity"

    if ENABLE_BLACKLIST and pw.lower() in [b.lower() for b in BLACKLIST]:
        return False, "blacklist"

    return True, None

def get_prompt(count, sector):
    """ create seeded prompt """
    batch_seed = uuid.uuid4().hex[:8]
    return f"""
    Generate {count} unique personas for a study on password habits in the {sector} sector.
    Batch Seed: {batch_seed} (Internal entropy seed).
    RESEARCH FOCUS: Credential Reuse.
    - Diversity: Global mix of names and backgrounds.
    - personal_password: Raw human root (hobbies, slang, pet names).
    - work_password: A modification of that root (12+ chars, numbers, symbols).
    Return a JSON list of objects: name, occupation, personal_email, personal_password, work_lanid, work_password, behavior_tag
    """

def write_files(all_personas):
    """ Refreshes all outputs. Uses 'w' to ensure clean CSV files on every batch. """
    # 1. JSON Master State
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(all_personas, f, indent=4)

    # 2. Credentials CSV (Clean overwrite)
    with open(OUTPUT_CSV, 'w', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["user_id", "password"])
        for p in all_personas:
            writer.writerow([p['personal_email'], p['personal_password']])
            writer.writerow([p['work_lanid'], p['work_password']])

    # 3. Summary Report
    with open(SUMMARY_FILE, "w") as f:
        f.write(f"=== STUDY SUMMARY | {time.ctime()} ===\n")
        f.write(f"Accepted: {stats['accepted']} | Attempts: {stats['total_generated']}\n")
        f.write(f"Rejections: ID Dupe: {stats['rejected_duplicate_persona']}, Forbidden/Emoji: {stats['rejected_forbidden']}, Complexity: {stats['rejected_complexity']}, BL: {stats['rejected_blacklist']}\n\n")

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

    # Recovery logic if script is restarted
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
        except Exception:
            pass

    while len(all_personas) < TARGET_COUNT:
        sector = target_sector_override if target_sector_override else SECTORS[len(all_personas) % len(SECTORS)]

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=get_prompt(CHUNK_SIZE, sector),
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

                # Validate BOTH to ensure no emojis in either column
                is_p_valid, p_reason = validate_password(p.get('personal_password', ''))
                is_w_valid, w_reason = validate_password(p.get('work_password', ''))

                if is_p_valid and is_w_valid:
                    p['sector'] = sector
                    valid_batch.append(p)
                    seen_ids.add(p_email)
                    seen_ids.add(w_id)
                    stats["accepted"] += 1
                    personal_pw_registry[p['personal_password']] += 1
                    work_pw_registry[p['work_password']] += 1
                else:
                    reason = p_reason if not is_p_valid else w_reason
                    if reason == "forbidden":
                        stats["rejected_forbidden"] += 1
                    elif reason == "complexity":
                        stats["rejected_complexity"] += 1
                    elif reason == "blacklist":
                        stats["rejected_blacklist"] += 1

            all_personas.extend(valid_batch)
            write_files(all_personas)

            print(f"[{sector}] Progress: {len(all_personas)}/{TARGET_COUNT} | Rejected Forbidden: {stats['rejected_forbidden']}")

        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    run_study()
