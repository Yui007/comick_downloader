import re

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a string to be a valid filename by removing or replacing
    characters that are not allowed in Windows filenames.
    """
    if not filename:
        return "unknown"
    
    # Remove the query string part of a URL
    filename = filename.split('?')[0]
    
    # Replace invalid filename characters with an underscore
    # Invalid chars: \ / : * ? " < > |
    sanitized = re.sub(r'[\\/:*?"<>|]', '_', filename)
    
    # Replace multiple spaces with a single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Remove leading/trailing spaces
    return sanitized.strip()