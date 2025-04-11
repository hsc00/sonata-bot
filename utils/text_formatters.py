def add_newline_limit(text, limit=50):
    if len(text) <= limit:
        return text  # If text is within the limit, return as is
    
    # Find the last space within the limit
    cut_off = text[:limit].rfind(" ")
    if cut_off == -1:  # If no space is found, split at the limit
        cut_off = limit

    # Insert a newline after the last word within the limit
    return text[:cut_off] + "\n" + text[cut_off:].strip()