#!/usr/bin/env python3
"""
Take a random sample from text files (fixed number or percentage).
Usage: python sample.py <size> <file1> <file2> ...
Example: python sample.py 10% shadow.txt pwdump.txt
"""
import sys
import random
import os
import math

def get_sample_size(total_lines, requested):
    """Calculate the final sample size based on integer or percentage string."""
    try:
        if requested.endswith('%'):
            percent = float(requested.strip('%')) / 100
            size = math.ceil(total_lines * percent)
        else:
            size = int(requested)

        # Ensure we don't try to sample more than exists
        return max(0, min(size, total_lines))
    except ValueError:
        print(f"Error: Invalid sample size format '{requested}'. Use '250' or '10%'.")
        sys.exit(1)

def process_sampling(requested_size, files):
    """ main loop to process files ###
    for file_path in files:
        if not os.path.isfile(file_path):
            print(f"Skipping: '{file_path}' (File not found)")
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            total_lines = len(lines)
            if total_lines == 0:
                print(f"Skipping: '{file_path}' (Empty file)")
                continue

            # Calculate how many records to pull
            n = get_sample_size(total_lines, requested_size)

            # Perform the random sample
            sample_data = random.sample(lines, n)

            # Create the new filename
            base_name = os.path.basename(file_path)
            output_name = f"sample_{base_name}"

            with open(output_name, 'w', encoding='utf-8') as f_out:
                f_out.writelines(sample_data)

            print(f"✅ Created {output_name}: Sampled {n} of {total_lines} records ({requested_size})")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python sample.py <number|percent> <file_paths...>")
        print("Examples:")
        print("  python sample.py 250 shadow.txt md5.txt")
        print("  python sample.py 10% sha256.txt pwdump.txt")
        sys.exit(1)

    requested_val = sys.argv[1]
    target_files = sys.argv[2:]

    process_sampling(requested_val, target_files)
