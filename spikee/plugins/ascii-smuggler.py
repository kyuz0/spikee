def encode_message(message, use_unicode_tags=True):
    encoded = []
    code_points = []
    invalid_chars = ""

    # Start tag if use_unicode_tags is True
    if use_unicode_tags:
        encoded.append(chr(0xE0001))
        code_points.append("U+E0001")

    # Process each character in the message
    for char in message:
        if 0x20 <= ord(char) <= 0x7E:  # Valid ASCII range (0x20 - 0x7E)
            code_point = 0xE0000 + ord(char)
            encoded.append(chr(code_point))
            code_points.append(f"U+{code_point:X}")
        else:
            invalid_chars += char
            encoded.append(char)

    # End tag if use_unicode_tags is True
    if use_unicode_tags:
        encoded.append(chr(0xE007F))
        code_points.append("U+E007F")

    # Optional status update about invalid characters
    status_message = (
        f"Invalid characters detected: {invalid_chars}" if invalid_chars else ""
    )

    return {
        "code_points": " ".join(code_points),
        "encoded": "".join(encoded),
        "status": status_message,
    }

def transform(text):
    """Convert ASCII text to Unicode Tags which are invisible in most UI elements, https://embracethered.com/blog/ascii-smuggler.html"""

    result = encode_message(text)
    return result["encoded"]
