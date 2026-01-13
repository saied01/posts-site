import re
from pathlib import Path
from uuid import uuid4

def normalize_filename(filename:str) -> str:
    name = Path(filename).stem
    ext = Path(filename).suffix.lower()

    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_\-]", "", name)

    return f"{name}{ext}"

def get_storage_name(filename:str) -> str:
    ext = Path(filename).suffix.lower()

    return f"{uuid4().hex}{ext}"
