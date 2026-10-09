""" generate "human-like" password for study - Gemini 3.8 Flash """
"""
Persona Password Study Data Generator - Gemini 3.8 Flash
Branch: passphrases
Generates realistic 3-tier credentials (Personal Root, Work Password, Work Passphrase)
incorporating human behavioral anchors, friction transformations, and dynamic prompt variation.
"""

import os
import re
import csv
import sys
import json
import time
import uuid
import string
import warnings
from collections import Counter
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import ClientError, APIError

try:
    from config import API_KEY
except ImportError:
    print("❌ ERROR: 'config.py' not found or missing 'API_KEY'.")
    print("   Please create config.py in the working directory containing: API_KEY = 'your_gemini_key'")
    sys.exit(1)

# --- SETTINGS ---
TARGET_COUNT = 2500
CHUNK_SIZE = 25
OUTPUT_JSON = "personas.json"
OUTPUT_CSV = "credentials.csv"
SUMMARY_FILE = "data_summary.txt"
SECTORS = ["Banking", "Healthcare", "Construction", "Education", "Retail", "Tech"]
MODEL_TARGET = "gemini-3.8-flash"

# Suppress benign google-genai SDK warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.genai")

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

# --- STRUCTURED OUTPUT SCHEMA ---
class Persona(BaseModel):
    name: str
    occupation: str
    personal_email: str
    personal_password: str
    work_lanid: str
    work_password: str
    work_passphrase: str
    behavior_tag: str

# --- SYSTEM INSTRUCTIONS ---
SYSTEM_INSTRUCTION = """
You are a synthetic data generator modeling human behavioral cybersecurity traits.
Your task is to generate realistic, highly diverse user personas across global cultures, subcultures, and job sectors.
Avoid relying on generic English baseline names (e.g., "John Smith") or standard office clichés.

For each persona, simulate how human friction and memory shortcuts shape their credential choices:
1. personal_password: Raw human root (short, meaningful root: hobby, food, pet, team, slang + simple number).
2. work_password: Complex policy adaptation of that root (12+ chars, mixed cases, numbers, symbols, department tags).
3. work_passphrase: A 15+ character passphrase constructed by expanding the persona's semantic root into 4+ words or a phrase.
   Simulate how a human naturally satisfies corporate complexity rules (e.g., capitalization, hyphens/spaces, embedded numbers, or punctuation) 
   without sacrificing their own ability to remember it.
"""

# --- REPORTING COUNTERS ---
stats = {
    "total_generated": 0,
    "rejected_complexity": 0,
    "rejected_blocklist": 0,
    "rejected_pattern": 0,
    "rejected_duplicate_persona": 0,
    "accepted": 0
}

personal_pw_registry = Counter()
work_pw_registry = Counter()
passphrase_registry = Counter()

client = genai.Client(api_key=API_KEY)

def validate_password(pw, check_complexity=True, is_passphrase=False):
    """ Validate credential string against character set and complexity rules """
    if not pw:
        return False, "empty"

    all_allowed = string.ascii_letters + string.digits + VALID_SYMBOLS + " -"
    if any(c not in all_allowed for c in pw):
        return False, "pattern"

    if check_complexity:
        min_len = 15 if is_passphrase else 12
        if len(pw) < min_len:
            return False, "complexity"

        has_low = any(c in string.ascii_lowercase for c in pw)
        has_up  = any(c in string.ascii_uppercase for c in pw)
        has_num = any(c in string.digits for c in pw)
        has_sym = any(c in (VALID_SYMBOLS + " -") for c in pw)

        if sum([has_low, has_up, has_num, has_sym]) < 3:
            return False, "complexity"

        if ENABLE_BLOCKLIST and pw.lower() in [b.lower() for b in BLOCKLIST]:
            return False, "blocklist"

    return True, None

def get_prompt(count, sector, exclusions_sample):
    """ Build dynamic prompt with seed and dynamic negative context """
    batch_seed = uuid.uuid4().hex[:8]
    exclusion_str = ", ".join(exclusions_sample) if exclusions_sample else "None"
    
    return f"""
    Batch Seed: {batch_seed}
    Sector: {sector}
    Target Count: {count}
    
    NEGATIVE DIVERSITY CONSTRAINT:
    Do NOT reuse or approximate the following recent personas or roots: [{exclusion_str}].
    Incorporate diverse sub-disciplines, niche regional foods/sports/interests, and distinct naming conventions.
    
    CREDENTIAL SPECIFICATIONS:
    - personal_password: Short root (e.g., 'baguette8', 'gatos2024', 'cricketfan').
    - work_password: Complex rule-compliant expansion (e.g., '!Baguette8Credit', 'Gatos2024$HomeLoan').
    - work_passphrase: Corporate passphrase built off the identity/root (15+ chars, 4+ words, e.g., 'Baguette-Credit-Vault-2026', 'i-Love-2-Eat-Hot-Baguettes!').
    
    Return a JSON list adhering to the schema.
    """

def write_summary():
    """ Write execution summary to disk """
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

        f.write("\n--- TOP 10 WORK PASSPHRASES ---\n")
        for pw, count in passphrase_registry.most_common(10):
            f.write(f"{pw}: {count}\n")

def run_study():
    """ Main persona generation loop """
    target_sector_override = sys.argv[1] if len(sys.argv) > 1 else None
    all_personas = []
    seen_ids = set()
    recent_names = []

    print("=" * 65)
    print(" 🛡️🧠 PERSONA PASSWORDS STUDY - SYNTHETIC DATA GENERATOR")
    print("=" * 65)

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
                    passphrase_registry[p.get('work_passphrase', '')] += 1
                    recent_names.append(p['name'])
            print(f"ℹ️ Loaded existing dataset: {len(all_personas)}/{TARGET_COUNT} personas.")
        except Exception as e:
            print(f"⚠️ Could not load existing '{OUTPUT_JSON}': {e}. Starting fresh.")

    if len(all_personas) >= TARGET_COUNT:
        print(f"\n✅ TARGET REACHED: {len(all_personas)} personas already exist in '{OUTPUT_JSON}'.")
        print("   If you want to generate a new run, archive or remove the existing files:")
        print("   $ mkdir archive_run && mv personas.json credentials.csv archive_run/")
        return

    print(f"🚀 Target set to {TARGET_COUNT} personas. Model: [{MODEL_TARGET}]")
    if target_sector_override:
        print(f"🎯 Sector Override: Focused strictly on [{target_sector_override}]")
    print("-" * 65)

    try:
        while len(all_personas) < TARGET_COUNT:
            sector = target_sector_override if target_sector_override else SECTORS[len(all_personas) % len(SECTORS)]
            request_count = min(CHUNK_SIZE, TARGET_COUNT - len(all_personas))

            # Dynamic Temperature Scaling: Increase temp if rejections spike
            rejection_ratio = stats["rejected_duplicate_persona"] / max(1, stats["total_generated"])
            current_temp = min(1.1, 0.7 + (rejection_ratio * 0.5))

            try:
                response = client.models.generate_content(
                    model=MODEL_TARGET,
                    contents=get_prompt(request_count, sector, recent_names[-20:]),
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        response_mime_type='application/json',
                        response_schema=list[Persona],
                        temperature=current_temp
                    )
                )

                if getattr(response, 'parsed', None):
                    batch_data = [item.model_dump() for item in response.parsed]
                else:
                    batch_data = json.loads(response.text)

                valid_batch = []
                for p in batch_data:
                    stats["total_generated"] += 1
                    p_email = p.get('personal_email', '').lower()
                    w_id = p.get('work_lanid', '').lower()

                    if not p_email or p_email in seen_ids or w_id in seen_ids:
                        stats["rejected_duplicate_persona"] += 1
                        continue

                    is_p_v, p_r = validate_password(p.get('personal_password', ''), check_complexity=False)
                    is_w_v, w_r = validate_password(p.get('work_password', ''), check_complexity=True)
                    is_pass_v, pass_r = validate_password(p.get('work_passphrase', ''), check_complexity=True, is_passphrase=True)

                    if is_p_v and is_w_v and is_pass_v:
                        p['sector'] = sector
                        valid_batch.append(p)
                        seen_ids.add(p_email)
                        seen_ids.add(w_id)
                        recent_names.append(p.get('name', ''))
                        stats["accepted"] += 1
                        
                        personal_pw_registry[p['personal_password']] += 1
                        work_pw_registry[p['work_password']] += 1
                        passphrase_registry[p['work_passphrase']] += 1
                    else:
                        reason = p_r if not is_p_v else (w_r if not is_w_v else pass_r)
                        if reason == "pattern":
                            stats["rejected_pattern"] += 1
                        elif reason == "complexity":
                            stats["rejected_complexity"] += 1
                        elif reason == "blocklist":
                            stats["rejected_blocklist"] += 1

                all_personas.extend(valid_batch)
                with open(OUTPUT_JSON, 'w') as f:
                    json.dump(all_personas, f, indent=4)

                # Write 3-tier credentials output block
                file_exists = os.path.exists(OUTPUT_CSV) and os.path.getsize(OUTPUT_CSV) > 0
                with open(OUTPUT_CSV, 'a', newline='') as f:
                    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                    if not file_exists:
                        writer.writerow(["user_id", "password"])
                    for p in valid_batch:
                        writer.writerow([p['personal_email'], p['personal_password']])
                        writer.writerow([p['work_lanid'], p['work_password']])
                        writer.writerow([p['work_lanid'], p['work_passphrase']])

                write_summary()

                print(f"📊 Progress: {len(all_personas)}/{TARGET_COUNT} | Sector: [{sector}] | Temp: [{current_temp:.2f}]")
                print(f"   [Rejections] Dupes: {stats['rejected_duplicate_persona']} | Complex: {stats['rejected_complexity']} | Pattern: {stats['rejected_pattern']}")

            except (ClientError, APIError) as api_err:
                err_str = str(api_err)
                if "402" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    print("\n🛑 BILLING / CREDIT DEPLETED ERROR (HTTP 402):")
                    print("   Your Google AI Studio project has run out of prepayment credits or quota limits.")
                    print("   👉 Manage billing: https://ai.studio/projects")
                    print("   👉 Learn more: https://ai.google.dev/gemini-api/docs/billing#prepay")
                    print("\n   Exiting cleanly. Progress saved to disk.")
                    sys.exit(1)
                elif "429" in err_str:
                    print("\n⏳ Rate limit hit (HTTP 429). Waiting 10 seconds before retry...")
                    time.sleep(10)
                else:
                    print(f"❌ API Error: {api_err}")
                    time.sleep(3)

            except Exception as parse_err:
                print(f"❌ Parse/Formatting Error: {parse_err}")
                time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n⏹️ Process interrupted by user (Ctrl+C).")
        print(f"   Saved {len(all_personas)} valid personas to '{OUTPUT_JSON}' and '{OUTPUT_CSV}'.")
        sys.exit(0)

if __name__ == "__main__":
    run_study()
