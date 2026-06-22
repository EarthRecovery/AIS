from functools import lru_cache
from pathlib import Path


@lru_cache()
def load_base_prompt() -> str:
    """Load base prompt from adjacent Jinja2 template file."""
    template_path = Path(__file__).with_suffix(".j2")
    return template_path.read_text(encoding="utf-8")


BASE_PROMPT = load_base_prompt()
