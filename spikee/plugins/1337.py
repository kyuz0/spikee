def transform(text):
    """Transforms the text into 1337 speak, ignoring URLs, markdown images, and HTML tags. 
       Ref: https://mindgard.ai/blog/bypassing-azure-ai-content-safety-guardrails"""
    import re

    leet_dict = {
        'A': '4', 'a': '4',
        'E': '3', 'e': '3',
        'I': '1', 'i': '1',
        'O': '0', 'o': '0',
        'T': '7', 't': '7',
        'S': '5', 's': '5',
        'B': '8', 'b': '8',
        'G': '6', 'g': '6',
        'Z': '2', 'z': '2'
    }

    # Regex patterns to match URLs, markdown images, and HTML tags
    url_regex = r'https?://[^\s]+'
    markdown_image_regex = r'!\[[^\]]*\]\([^\)]+\)'
    html_tag_regex = r'<[^>]+>'
    special_patterns_regex = r'(' + '|'.join([url_regex, markdown_image_regex, html_tag_regex]) + r')'

    # Split the text into chunks, including the special patterns
    chunks = re.split(special_patterns_regex, text)

    # Process each chunk
    transformed_chunks = []
    for chunk in chunks:
        if chunk is None or chunk == '':
            continue
        if re.fullmatch(special_patterns_regex, chunk):
            # Special pattern, leave it as is
            transformed_chunks.append(chunk)
        else:
            # Transform the chunk
            transformed_chunk = ''.join(leet_dict.get(c, c) for c in chunk)
            transformed_chunks.append(transformed_chunk)

    # Reconstruct the text
    transformed_text = ''.join(transformed_chunks)
    return transformed_text
