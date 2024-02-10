#!/usr/bin/env python

import random
import json

MINWORDS=1
MAXWORDS=3

def load_words_from_file(filepath='/usr/share/dict/linux.words'):
    try:
        with open(filepath, 'r') as file:
            words = file.read().splitlines()
        return words
    except FileNotFoundError:
        print(f"Word file not found at {filepath}. Please check the path and try again.")
        return []

def generate_random_phrase(word_list):
    num_words = random.randint(MINWORDS, MAXWORDS)
    return ' '.join(random.choice(word_list) for _ in range(num_words))

# Load words from the specified file
english_words = load_words_from_file()

# Check if words were loaded successfully
if not english_words:
    english_words = ['apple', 'banana', 'cherry']  # Fallback to a minimal list

data = []

# Generate 10 dictionaries, each with 10 random English words as values for the keys
for _ in range(10):
    keys = [f'key{i}' for i in range(1, 11)]
    random.shuffle(keys)  # Shuffle the order of keys
    random_dict = {key: generate_random_phrase(english_words) for key in keys}
    data.append(random_dict)

# Use json.dumps for formatted output
#formatted_output = json.dumps(data, indent=1)[1:-1]  # Slice to remove the outer square brackets
formatted_output = json.dumps(data, indent=1)
print(formatted_output)
