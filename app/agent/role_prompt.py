from functools import lru_cache
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pathlib import Path

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
    return template.render(role=role_settings)