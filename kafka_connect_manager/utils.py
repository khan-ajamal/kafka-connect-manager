"""utils.py contains supporting variable and methods"""
import os
import re

STATE_COLOR_MAP = {"RUNNING": "[bold green]"}

# used to remove non url safe characters
TRANSLATE_TABLE = {i: "" for i in range(128) if not re.match(r"[A-Za-z0-9\s]", chr(i))}

ENV_VARIABLE_PATTERN = r"(\$\{[A-Z0-9\_]+\})"


def get_formatted_state(state: str) -> str:
    """Format state for rich console"""
    return f"{STATE_COLOR_MAP[state]}{state}"


def slugify(text: str) -> str:
    """slugify given text to make it URL safe"""
    text = text.translate(TRANSLATE_TABLE)
    text = "-".join(text.split())
    return text


def expand_environment_variables(connector_config: dict):
    """Expand environment variables

    Replaces ${ENV_VARIABLE} with actual value if its available
    """
    for k, v in connector_config.items():
        if isinstance(v, dict):
            expand_environment_variables(connector_config[k])
        elif isinstance(v, str) and re.findall(ENV_VARIABLE_PATTERN, v):
            connector_config[k] = os.path.expandvars(v)
