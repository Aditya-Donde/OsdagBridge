import platform
import os
from pathlib import Path

KEY_MODULE = "Module"

def get_documents_folder():
    system = platform.system()

    if system == "Windows":
        # Windows: typically C:\Users\Username\Documents
        docs_path = Path.home() / "Documents"
        if not docs_path.exists():
            docs_path = Path.home() / "OneDrive" / "Documents"
    elif system == "Darwin":  # macOS
        # macOS: typically /Users/Username/Documents
        docs_path = Path.home() / "Documents"
    elif system == "Linux":
        # Linux: typically /home/username/Documents
        # Also check XDG_DOCUMENTS_DIR for custom locations
        xdg_docs = os.environ.get("XDG_DOCUMENTS_DIR")
        if xdg_docs:
            docs_path = Path(xdg_docs)
        else:
            docs_path = Path.home() / "Documents"
    else:
        # Fallback to home directory for unknown systems
        docs_path = Path.home()

    # Ensure the directory exists, otherwise fall back to home
    if not docs_path.exists():
        docs_path = Path.home()
    return str(docs_path)