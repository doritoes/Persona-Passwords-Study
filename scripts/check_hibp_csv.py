#!/usr/bin/env python3
"""
parse password research data, look up on HIBP
https://haveibeenpwned.com/API/v3#SearchingPwnedPasswordsByRange
enrich the CSV data with the results, and output the combined results
"""
import os
import csv
import sys
import time
import hashlib
import requests

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
    """ main loop to process the input file """
    output_file = f"checked_{input_file}"
    pwned_list = []
    total_count = 0
    pwned_count = 0

    try:
        with open(input_file, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames + ['pwned']

            with open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                writer.writeheader()

                for row in reader:
                    total_count += 1
                    password = row.get('password', '')
                    count = get_pwned_count(password)

                    is_pwned = count > 0
                    row['pwned'] = is_pwned

                    if is_pwned:
                        pwned_count += 1
                        pwned_list.append(password)
                        print(f"⚠️  PWNED: {row['user_id']}")
                    else:
                        print(f"✅ SAFE: {row['user_id']}")

                    writer.writerow(row)
                    time.sleep(0.2) # Rate limit precaution

        # Final Report
        print("\n" + "="*40)
        print("FINAL SECURITY REPORT")
        print("="*40)
        if total_count > 0:
            percentage = (pwned_count / total_count) * 100
            print(f"Total Passwords Checked: {total_count}")
            print(f"Pwned Passwords Found:  {pwned_count}")
            print(f"Sector Compromise Rate: {percentage:.2f}%")

            if pwned_list:
                print("\nList of Compromised Passwords:")
                for p in set(pwned_list): # Using set to show unique passwords
                    print(f" - {p}")
        else:
            print("No data processed.")

        print(f"\nResults saved to: {output_file}")

    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {os.path.basename(sys.argv[0])} <credentials.csv>")
        sys.exit(1)

    process_csv(sys.argv[1])
