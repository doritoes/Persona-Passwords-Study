#!/usr/bin/env python3
import csv
import hashlib
import requests
import time
import sys
import os

def check_hibp_api(hash_prefix):
    """Fetch all hash suffixes with retry logic for rate limits."""
    url = f"https://api.pwnedpasswords.com/range/{hash_prefix}"
    while True:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text
            if response.status_code == 429:
                wait_time = int(response.headers.get("Retry-After", 2))
                print(f"--- Rate limited. Sleeping {wait_time}s... ---")
                time.sleep(wait_time)
                continue
            return None
        except requests.exceptions.RequestException:
            return None

def get_pwned_count(password):
    """Returns the count of times a password was pwned."""
    if not password:
        return 0
    sha1 = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    
    response_list = check_hibp_api(prefix)
    if not response_list:
        return 0

    for line in response_list.splitlines():
        h, count = line.split(':')
        if h == suffix:
            return int(count)
    return 0

def process_csv(input_file):
    output_file = f"checked_{input_file}"
    
    # We use quoting=csv.QUOTE_ALL to match your input style
    try:
        with open(input_file, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames + ['pwned']

            with open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                writer.writeheader()

                for row in reader:
                    password = row.get('password', '')
                    count = get_pwned_count(password)
                    
                    # Store as True/False as requested
                    row['pwned'] = True if count > 0 else False
                    
                    status = "⚠️  PWNED" if row['pwned'] else "✅ SAFE"
                    print(f"{status}: {row['user_id']}")
                    
                    writer.writerow(row)
                    time.sleep(0.2) # Ethics/Rate limit buffer

        print(f"\nProcessing complete. Results saved to: {output_file}")

    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {os.path.basename(sys.argv[0])} <input_passwords.csv>")
        sys.exit(1)
    
    process_csv(sys.argv[1])
