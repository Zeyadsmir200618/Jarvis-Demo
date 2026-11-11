import os
from pathlib import Path
from app.core.config import GENERATED_SITES_DIR

def write_file(file_path: str, content: str) -> str:
    """Writes content to a specified file path. If the directory does not exist, it will be created.
    Args:
        file_path (str): The full path to the file, e.g., 'path/to/my_file.txt'
        content (str): The content to write to the file.
    Returns:
        str: A success message with the file path.
    """
    try:
        full_path = Path(file_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File successfully written to: {full_path}"
    except Exception as e:
        return f"Error writing file {file_path}: {str(e)}"

def generate_website_file(relative_path: str, content: str) -> str:
    """Generates a file within the GENERATED_SITES_DIR for website content.
    Args:
        relative_path (str): The path relative to GENERATED_SITES_DIR, e.g., 'login.html' or 'css/style.css'
        content (str): The content of the file.
    Returns:
        str: A success message with the full path and a URL if it's an HTML file, or an error message.
    """
    full_path = GENERATED_SITES_DIR / relative_path
    response = write_file(str(full_path), content)

    if "Error" in response:
        return response

    # If it's an HTML file, provide a preview URL
    if full_path.suffix == ".html":
        # Assuming GENERATED_SITES_DIR is served statically by a web server
        # For now, we'll give a placeholder or a local path representation
        preview_url = f"/generated_sites/{relative_path}"
        return f"{response}. Preview available at: {preview_url}"
    return response
