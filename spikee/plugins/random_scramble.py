"""
random_scramble.py

Implements text augmentations from Appendix A.1 of:
  "Best-of-N Jailbreaking"
  John Hughes et al., 2024
  (https://arxiv.org/html/2412.03556v1#A1)

Transformations (applied to normal text chunks, skipping URLs/HTML/Markdown images):
  1) Character scrambling (p=0.6) - For words of length >=4, shuffle the middle
     characters, keeping the first & last char fixed.
  2) Random capitalization (p=0.6) - Each character has a 60% chance
     to become uppercase.
  3) Character noising (p=0.06) - Each character in ASCII range [32..126]
     has a 6% chance to have its ASCII index +/-1 (randomly).

Any segments matching special patterns (URLs, HTML tags, Markdown images) are
left completely unaltered.

Usage:
  spikee test --dataset my_dataset.jsonl --target my_target \
              --adaptive-attack random_scramble \
              --adaptive-attack-iterations 50

This plugin is designed for "adaptive" or iterative attacks, generating new
variations each time `transform(text)` is called.
"""

import re
import random

# Regex to detect special patterns we do NOT modify
url_regex = r'https?://[^\s]+'
markdown_image_regex = r'!\[[^\]]*\]\([^\)]+\)'
html_tag_regex = r'<[^>]+>'
special_patterns_regex = f"({url_regex}|{markdown_image_regex}|{html_tag_regex})"

# Probability constants from the paper
SCRAMBLE_PROB = 0.6         # for scrambling the middle of words
CAPITALIZATION_PROB = 0.6   # for random capitalization
NOISE_PROB = 0.06           # for ASCII +/- 1

def transform(text: str) -> str:
    """
    Splits the text into segments. Any segment matching `special_patterns_regex`
    (URL, HTML tag, or Markdown image) is returned verbatim. Non-matching
    segments are augmented according to the paper:

      - With p=0.6, scramble the middle letters of words >=4 chars
      - For each character, with p=0.6, uppercase it
      - For each character [ASCII 32..126], with p=0.06, add or subtract 1 from ASCII code
    """
    # Split into special patterns vs. normal text
    chunks = re.split(special_patterns_regex, text)
    if not chunks:
        return text

    result_chunks = []
    for chunk in chunks:
        if not chunk:
            continue

        # If it's exactly a special pattern, leave as is
        if re.fullmatch(special_patterns_regex, chunk):
            result_chunks.append(chunk)
        else:
            # Apply transformations to this "normal" text chunk
            transformed = _augment_text(chunk)
            result_chunks.append(transformed)

    return ''.join(result_chunks)

def _augment_text(normal_text: str) -> str:
    """
    Applies the three transformations to normal text:
      1) Word-level scramble (p=0.6)
      2) Random capitalization (p=0.6)
      3) Character noising (p=0.06)
    """

    # 1) Scramble the middle of words with probability 0.6
    #    We'll treat "words" as sequences of letters (or letters+digits).
    words = re.split(r'(\s+)', normal_text)  # keep whitespace as separate tokens
    scrambled_words = []
    for token in words:
        # If token is purely whitespace, skip
        if re.fullmatch(r'\s+', token):
            scrambled_words.append(token)
            continue

        # Possibly scramble middle of each word (if length >= 4)
        scrambled_words.append(_maybe_scramble_words(token))

    # Now we have a single string again
    scrambled_str = ''.join(scrambled_words)

    # 2) For each character, uppercase with p=0.6
    # 3) For each character in [32..126], noise with p=0.06
    final_chars = []
    for char in scrambled_str:
        # random capitalization
        if random.random() < CAPITALIZATION_PROB:
            # Convert to uppercase (if it's a letter)
            char = char.upper()

        # character noising
        ascii_code = ord(char)
        if 32 <= ascii_code <= 126 and random.random() < NOISE_PROB:
            # choose +/-1
            delta = random.choice([-1, 1])
            new_code = ascii_code + delta
            # clamp or skip if out of range?
            if 32 <= new_code <= 126:
                char = chr(new_code)
            # else we do nothing if the shift is out-of-range

        final_chars.append(char)

    return ''.join(final_chars)

def _maybe_scramble_words(token: str) -> str:
    """
    For each word in 'token' (split on punctuation?), with p=SCRAMBLE_PROB,
    scramble the middle of the word if word length >= 4.

    We'll keep the first & last char fixed, shuffle the middle.
    Otherwise, we leave the token as is.
    """
    # We'll treat anything separated by non-alphanumeric as separate "subwords"
    subwords = re.split(r'([^a-zA-Z0-9]+)', token)
    scrambled_subwords = []
    for sub in subwords:
        if not sub or re.fullmatch(r'[^a-zA-Z0-9]+', sub):
            # punctuation or separator, keep as is
            scrambled_subwords.append(sub)
            continue

        # sub is a "word" of letters/digits
        if len(sub) >= 4 and random.random() < SCRAMBLE_PROB:
            # scramble the middle
            middle = list(sub[1:-1])
            random.shuffle(middle)
            sub = sub[0] + ''.join(middle) + sub[-1]

        scrambled_subwords.append(sub)

    return ''.join(scrambled_subwords)
