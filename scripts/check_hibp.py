""" Check the provided password file against HIBP"""
import os
import sys
import time
import hashlib
import requests

def check_hibp_api(hash_prefix):
    """Fetch all hash suffixes with retry logic for rate limits."""
    url = f"https://api.pwnedpasswords.com/range/{hash_prefix}"

    while True:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text
        if response.status_code == 429:
            # Look for 'Retry-After' header, default to 2 seconds if not found
            wait_time = int(response.headers.get("Retry-After", 2))
            print(f"--- Rate limited. Sleeping for {wait_time} seconds... ---")
            time.sleep(wait_time)
            continue # Try the request again after sleeping
        raise RuntimeError(f"Error fetching: {response.status_code}")

def get_password_leaks_count(hashes, hash_to_check):
    """Check if our specific hash suffix is in the returned list."""
    hashes = (line.split(':') for line in hashes.splitlines())
    for h, count in hashes:
        if h == hash_to_check:
            return int(count)
    return 0

def pwned_api_check(password):
    """Full check logic: hash, prefix, query, and match."""
    sha1password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1password[:5], sha1password[5:]
    response_list = check_hibp_api(prefix)
    return get_password_leaks_count(response_list, suffix)

def main(file_path):
    """Main loop"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                password = line.strip()
                if not password:
                    continue
                count = pwned_api_check(password)
                if count:
                    print(f"⚠️  '{password}' was found {count} times.")
                else:
                    print(f"✅ '{password}' was NOT found.")
                # Small preventive delay to avoid hitting the limit constantly
                time.sleep(0.2)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Get the script name (like $0 in shell)
    script_name = os.path.basename(sys.argv[0])

    if len(sys.argv) == 2:
        target_file = sys.argv[1]
        # Verify the file exists before starting
        if os.path.isfile(target_file):
            main(target_file)
        else:
            print(f"Error: The file '{target_file}' does not exist.")
            sys.exit(1)
    else:
        print(f"Usage: python {script_name} <password_file.txt>")
        sys.exit(1)
