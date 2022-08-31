"""__main__.py is used to support module execution of package
python -m kafka_connect_manager
"""
from kafka_connect_manager.cli import app

app(prog_name="kcm")
