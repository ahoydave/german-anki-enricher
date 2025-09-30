#!/usr/bin/env python3
"""
Script to run the German Anki generator on new_words.txt and append to added_words.txt
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    # Define file paths
    new_words_file = "new_words.txt"
    added_words_file = "added_words.txt"
    output_file = "generated_deck.apkg"
    
    # Check if new_words.txt exists
    if not os.path.exists(new_words_file):
        print(f"Error: {new_words_file} not found.")
        print(f"Please create {new_words_file} with your German/English words (one per line).")
        sys.exit(1)
    
    # Check if new_words.txt is empty
    with open(new_words_file, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not words:
        print(f"Error: {new_words_file} is empty or contains no valid words.")
        sys.exit(1)
    
    print(f"Found {len(words)} words in {new_words_file}")
    print(f"Running German Anki generator...")
    
    # Run the German Anki generator
    try:
        cmd = [
            "uv", "run", "python", "german_anki_generator.py", 
            new_words_file, 
            "--output", output_file
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Generator output:")
        print(result.stdout)
        
        if result.stderr:
            print("Generator warnings/errors:")
            print(result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"Error running generator: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'uv' command not found. Please make sure uv is installed and in your PATH.")
        sys.exit(1)
    
    # Append words to added_words.txt
    print(f"Appending words to {added_words_file}...")
    
    try:
        # Read existing content if file exists
        existing_words = set()
        if os.path.exists(added_words_file):
            with open(added_words_file, 'r', encoding='utf-8') as f:
                existing_words = {line.strip() for line in f if line.strip() and not line.startswith('#')}
        
        # Append new words (avoid duplicates)
        new_words_to_add = []
        for word in words:
            if word not in existing_words:
                new_words_to_add.append(word)
                existing_words.add(word)
        
        if new_words_to_add:
            with open(added_words_file, 'a', encoding='utf-8') as f:
                for word in new_words_to_add:
                    f.write(f"{word}\n")
            print(f"Added {len(new_words_to_add)} new words to {added_words_file}")
        else:
            print("All words were already in added_words.txt")
            
    except Exception as e:
        print(f"Error updating {added_words_file}: {e}")
        sys.exit(1)
    
    print(f"\nSummary:")
    print(f"  Generated deck: {output_file}")
    print(f"  Updated: {added_words_file}")
    print(f"  Processed: {len(words)} words")


if __name__ == "__main__":
    main()
