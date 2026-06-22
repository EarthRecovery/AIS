from functools import lru_cache
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pathlib import Path


def _normalize_role_settings(role_settings) -> dict:
    """Ensure template always sees all expected keys to avoid StrictUndefined errors."""
    if role_settings is None:
        role = {}
    elif isinstance(role_settings, dict):
        role = dict(role_settings)
    else:
        role = role_settings.__dict__.copy() if hasattr(role_settings, "__dict__") else {}

    defaults = {
        "name": "",
        "description": "",
        "worldview": "",
        "personality": [],
        "scenario": "",
        "example_dialogues": [],
    }
    for key, default in defaults.items():
        role.setdefault(key, default)
    return role


def load_role_prompt(role_settings) -> str:
    """Load role prompt from adjacent Jinja2 template file."""
    template_dir = Path(__file__).parent
    env = Environment(
        loader=FileSystemLoader(template_dir),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template("role_prompt.j2")
    return template.render(role=_normalize_role_settings(role_settings))
