"""utils.py contains supporting variable and methods"""

STATE_COLOR_MAP = {"RUNNING": "[bold green]"}


def get_formatted_state(state):
    """Format state for rich console"""
    return f"{STATE_COLOR_MAP[state]}{state}"
