"""
best_of_n.py

Implements text augmentations from Appendix A.1 of:
  "Best-of-N Jailbreaking"
  John Hughes et al., 2024
  (https://arxiv.org/html/2412.03556v1#A1)

Transformations (applied to normal text chunks):
  1) Character scrambling (p=0.6) - For words of length >= 4, shuffle the middle
     characters, keeping the first & last character fixed.
  2) Random capitalization (p=0.6) - Each character has a 60% chance to become uppercase.
  3) Character noising (p=0.06) - Each character in ASCII range [32..126] has a 6% chance
     to have its ASCII code increased or decreased by 1.

Any substring that exactly matches one of the user-supplied exclusion regexes
(in the parameter `exclude_patterns`) is left completely unaltered.

This version of the plugin returns a list of 100 augmented samples.
"""

import re
import random
from typing import List

SCRAMBLE_PROB = 0.6       
CAPITALIZATION_PROB = 0.6   
NOISE_PROB = 0.06        

def transform(text: str, exclude_patterns: List[str] = None) -> List[str]:
    """
    Generates a list of 100 augmented samples from the input text.
    
    If exclude_patterns is provided (a list of regex strings), these are combined into a
    compound regex. The text is then split using this compound regex so that any substring
    that exactly matches one of the patterns is left untransformed.
    
    Returns:
        List[str]: A list of 100 independently generated augmented samples.
    """
    samples = []
    for _ in range(100):
        samples.append(_scramble_text(text, exclude_patterns))
    return samples

def _scramble_text(text: str, exclude_patterns: List[str] = None) -> str:
    """
    Processes the input text by splitting it into chunks based on the user‐supplied
    exclusion patterns. Any chunk that exactly matches the compound exclusion regex
    is preserved; all other chunks are augmented.
    """
    if exclude_patterns:
        compound = "(" + "|".join(exclude_patterns) + ")"
        chunks = re.split(compound, text)
        compound_re = re.compile(compound)
    else:
        chunks = [text]
        compound_re = None

    result_chunks = []
    for chunk in chunks:
        if compound_re and compound_re.fullmatch(chunk):
            # This chunk exactly matches one of the exclusion regexes – leave it unchanged.
            result_chunks.append(chunk)
        else:
            result_chunks.append(_augment_text(chunk))
    return "".join(result_chunks)

def _augment_text(normal_text: str) -> str:
    """
    Applies three transformations to the normal text:
      1) For each token of length ≥ 4, scramble its middle letters with probability SCRAMBLE_PROB.
      2) Randomly capitalize letters with probability CAPITALIZATION_PROB.
      3) Apply character noising (shift ASCII ±1) with probability NOISE_PROB.
      
    The text is first split on whitespace so that spacing is preserved.
    """
    tokens = re.split(r'(\s+)', normal_text)
    transformed_tokens = []
    for token in tokens:
        if token.strip() == "":
            transformed_tokens.append(token)
        else:
            transformed_tokens.append(_maybe_scramble_words(token))
    scrambled = "".join(transformed_tokens)
    result_chars = []
    for c in scrambled:
        if random.random() < CAPITALIZATION_PROB:
            c = c.upper()
        code = ord(c)
        if 32 <= code <= 126 and random.random() < NOISE_PROB:
            delta = random.choice([-1, 1])
            new_code = code + delta
            if 32 <= new_code <= 126:
                c = chr(new_code)
        result_chars.append(c)
    return "".join(result_chars)

def _maybe_scramble_words(token: str) -> str:
    """
    Splits the token into subwords using non-alphanumeric delimiters and, for each subword
    of length ≥ 4, scrambles its middle letters with probability SCRAMBLE_PROB while keeping
    the first and last character unchanged.
    """
    subwords = re.split(r'([^a-zA-Z0-9]+)', token)
    scrambled_subwords = []
    for sub in subwords:
        if not sub or re.fullmatch(r'[^a-zA-Z0-9]+', sub):
            scrambled_subwords.append(sub)
        else:
            if len(sub) >= 4 and random.random() < SCRAMBLE_PROB:
                middle = list(sub[1:-1])
                random.shuffle(middle)
                sub = sub[0] + "".join(middle) + sub[-1]
            scrambled_subwords.append(sub)
    return "".join(scrambled_subwords)
