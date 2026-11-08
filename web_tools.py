import httpx
from bs4 import BeautifulSoup

def fetch_web_content(url: str) -> str:
    """Fetches the content of a given URL.
    Args:
        url (str): The URL to fetch.
    Returns:
        str: The text content of the webpage or an error message.
    """
    try:
        response = httpx.get(url, follow_redirects=True, timeout=10.0)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract readable text, remove script and style tags
        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()
        text = soup.get_text()
        # Break into lines and remove leading/trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-hyphenated words and remove empty lines
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text[:4000] + "... (truncated)" if len(text) > 4000 else text # Truncate to avoid context window issues
    except httpx.RequestError as e:
        return f"Error fetching {url}: {e}"
    except Exception as e:
        return f"An unexpected error occurred while fetching {url}: {e}"
