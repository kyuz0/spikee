"""
prompt_decomposition_dumb.py

This plugin decomposes a prompt into up to 5 parts using basic heuristics,
labels them (e.g., PART1, STRING_2), and generates several naive reformulations.

Parts are randomly shuffled before reconstruction, to challenge positional bias
and force semantic parsing.

This is a non-LLM, deterministic version of `prompt_decomposition`.

Usage:
    spikee generate --plugins prompt_decomposition_dumb
"""

from typing import List, Union
import random

def transform(text: str, exclude_patterns: List[str] = None) -> Union[str, List[str]]:
    """
    Splits the input into labeled chunks, shuffles them, and outputs 5 naive structured rewrites.

    Args:
        text (str): The input prompt.
        exclude_patterns (List[str], optional): Ignored.

    Returns:
        List[str]: A list of shuffled prompt rephrasings.
    """
    words = text.strip().split()
    if not words:
        return [text]

    # Decide number of parts (up to 5)
    num_parts = min(len(words), 5)
    part_size = max(1, len(words) // num_parts)

    # Create chunks
    parts = []
    for i in range(num_parts):
        start = i * part_size
        end = start + part_size if i < num_parts - 1 else len(words)
        chunk = " ".join(words[start:end])
        parts.append((i + 1, chunk))  # (part_number, content)

    # Create labeled parts
    part_labels = [f"PART{n}: {text}" for n, text in parts]
    string_labels = [f"STRING_{n}: {text}" for n, text in parts]
    variable_labels = [f"VARIABLE_{n}: {text}" for n, text in parts]

    # Shuffle labels
    random.shuffle(part_labels)
    random.shuffle(string_labels)
    random.shuffle(variable_labels)

    # Create variations
    variations = [
        " → Answer this: " + " ".join(part_labels),
        "Interpret and respond using: " + " + ".join(variable_labels),
        "Given the following: " + " | ".join(string_labels) + " → What’s your response?",
        "Analyze by part: " + "; ".join(part_labels),
        "Use these variables in any order: " + " THEN ".join(variable_labels),
    ]

    return variations
