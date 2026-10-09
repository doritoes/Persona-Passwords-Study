#!/usr/bin/env python3
"""
Generate shadow, pwdump, and raw hash files from an input CSV.

Required: pip install passlib
"""
import os
import csv
import sys
import time
import hashlib
from concurrent.futures import ProcessPoolExecutor
from passlib.hash import sha512_crypt, nthash

def generate_shadow_line(user, password):
    """Create example Linux shadow file line using SHA-512 crypt ($6$)."""
    shadow_hash = sha512_crypt.hash(password)
    clean_user = user.split('@')[0].lower()
    return f"{clean_user}:{shadow_hash}:20386:0:99999:7:::"

def generate_pwdump_line(user, password, uid):
    """Create example Windows PWDUMP (NTLM) line."""
    ntlm = nthash.hash(password).upper()
    lm_empty = "aad3b435b51404eeaad3b435b51404ee"
    return f"{user}:{uid}:{lm_empty}:{ntlm}:::"

def process_single_row(args):
    """Worker function for parallel hash processing."""
    i, user, password, start_uid = args
    shadow_line = generate_shadow_line(user, password)
    pwdump_line = generate_pwdump_line(user, password, start_uid + i)

    encoded_pw = password.encode('utf-8')
    md5_hash = hashlib.md5(encoded_pw).hexdigest()
    sha1_hash = hashlib.sha1(encoded_pw).hexdigest()
    sha256_hash = hashlib.sha256(encoded_pw).hexdigest()

    return shadow_line, pwdump_line, md5_hash, sha1_hash, sha256_hash

def process_credentials(input_file):
    """Main loop with multiprocessing and terminal feedback."""
    start_uid = 1001

    try:
        with open(input_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = [r for r in reader if r.get('password')]

        total = len(rows)
        num_workers = os.cpu_count() or 4
        print(f"--- Processing {input_file} ({total} entries) ---")
        print(f"⚡ Parallelizing SHA-512 Crypt across {num_workers} CPU cores...")

        tasks = [
            (i, r.get('user_id', f'user_{i}'), r.get('password', ''), start_uid)
            for i, r in enumerate(rows)
        ]

        shadow_output = []
        pwdump_output = []
        md5_list = []
        sha1_list = []
        sha256_list = []

        start_time = time.time()
        completed = 0

        # Execute CPU-intensive hashing across worker pool
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            for result in executor.map(process_single_row, tasks, chunksize=25):
                s_line, p_line, m5, s1, s256 = result
                shadow_output.append(s_line)
                pwdump_output.append(p_line)
                md5_list.append(m5)
                sha1_list.append(s1)
                sha256_list.append(s256)

                completed += 1
                if completed % 50 == 0 or completed == total:
                    elapsed = time.time() - start_time
                    rate = completed / max(0.1, elapsed)
                    eta = (total - completed) / max(0.1, rate)
                    pct = (completed / total) * 100
                    print(
                        f"\r⏳ Progress: {completed}/{total} ({pct:.1f}%) | "
                        f"Speed: {rate:.1f} hashes/s | "
                        f"ETA: {int(eta)}s  ",
                        end="",
                        flush=True
                    )

        print("\n\nWriting dump files...")
        files_to_write = {
            "shadow.txt": shadow_output,
            "pwdump.txt": pwdump_output,
            "md5.txt": md5_list,
            "sha1.txt": sha1_list,
            "sha256.txt": sha256_list
        }

        for filename, content in files_to_write.items():
            with open(filename, "w", encoding="utf-8") as out_f:
                out_f.write("\n".join(content) + "\n")
            print(f"✅ Created {filename} ({len(content)} entries)")

        print(f"✨ All done in {time.time() - start_time:.1f} seconds.")

    except FileNotFoundError:
        print(f"Error: '{input_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 {os.path.basename(sys.argv[0])} <credentials.csv>")
        sys.exit(1)

    process_credentials(sys.argv[1])
