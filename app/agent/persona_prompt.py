from functools import lru_cache
from pathlib import Path


@lru_cache()
def load_persona_prompt() -> str:
    """Load persona prompt from adjacent Jinja2 template file."""
    template_path = Path(__file__).with_suffix(".j2")
    return template_path.read_text(encoding="utf-8")


PERSONA_PROMPT = load_persona_prompt()
