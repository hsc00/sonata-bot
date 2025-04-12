import re


def add_newline_limit(text, limit=45):
    if len(text) <= limit:
        return text  # If text is within the limit, return as is
    
    # Find the last space within the limit
    cut_off = text[:limit].rfind(" ")
    if cut_off == -1:  # If no space is found, split at the limit
        cut_off = limit

    # Insert a newline after the last word within the limit
    return text[:cut_off] + "\n" + text[cut_off:].strip()

def get_user_id(string):
    # Use regex to find the user id
    match = re.search(r'<@(\d+)>', string)
    if match:
        user_id = match.group(1)  # Extract only the numeric part
        # Remove the user id from the original string
        release_query = re.sub(r'<@\d+>', '', string).strip()
        return release_query, user_id  # Return the modified string and user_id separately
    
    return string, None  # Return original string and None if no mention is found