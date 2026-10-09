#!/usr/bin/env python3
"""
Generate shadow, pwdump, and raw hash files from an input CSV.

Required: pip install passlib
"""
import os
import csv
import sys
import hashlib
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

def process_credentials(input_file):
    """ main loop to process credentials """
    shadow_output = []
    pwdump_output = []
    md5_list = []
    sha1_list = []
    sha256_list = []

    start_uid = 1001

    try:
        with open(input_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            print(f"--- Processing {input_file} ---")
            for i, row in enumerate(reader):
                user = row.get('user_id', f'user_{i}')
                password = row.get('password', '')

                if not password:
                    continue

                # Generate standard hash formats
                shadow_output.append(generate_shadow_line(user, password))
                pwdump_output.append(generate_pwdump_line(user, password, start_uid + i))

                encoded_pw = password.encode('utf-8')
                md5_list.append(hashlib.md5(encoded_pw).hexdigest())
                sha1_list.append(hashlib.sha1(encoded_pw).hexdigest())
                sha256_list.append(hashlib.sha256(encoded_pw).hexdigest())

        # Write to original default filenames
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

    except FileNotFoundError:
        print(f"Error: '{input_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 {os.path.basename(sys.argv[0])} <credentials.csv>")
        sys.exit(1)

    process_credentials(sys.argv[1])
