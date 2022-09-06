"""cli.py contains cli commands"""
import json
import asyncio
from pathlib import Path
from types import SimpleNamespace

import typer

from kafka_connect_manager import constants
from kafka_connect_manager.main import (
    get_connectors,
    get_connector_status,
    register_connector,
)

app = typer.Typer(help="CLI to manage Kafka Connectors")


@app.callback()
def main(
    ctx: typer.Context,
    host: str = typer.Option(
        "http://localhost:8083", help="Connect worker host", envvar="CONNECT_HOST"
    ),
):
    """Method used to setup common context"""
    if not host:
        print("Missing connect worker host; pass --host or set env[CONNECT_HOST]")
        raise typer.Exit(1)

    if host[-1] == "/":
        host = host[:-1]
    ctx.obj = SimpleNamespace(host=host)


@app.command("list")
def list_connectors(
    ctx: typer.Context,
    connector_type: constants.ConnectorType = typer.Option(
        constants.ConnectorType.ALL.value,
        "--type",
        help="Type of connectors to list",
    ),
):
    """List all connectors"""
    asyncio.run(get_connectors(ctx.obj.host, connector_type))


@app.command("status")
def connectors_status(
    ctx: typer.Context,
    connector_name: str = typer.Option(
        ...,
        "--connector",
        help="Name of connector",
    ),
):
    """Get status connector"""
    asyncio.run(get_connector_status(ctx.obj.host, connector_name))


@app.command("add")
def add_connector(
    ctx: typer.Context,
    configuration_file: Path = typer.Option(
        ...,
        "--file",
        "-f",
        help="Config JSON file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
):
    """Register new connector

    Supporting environment variable expansion in JSON file.

    A connector requires a name and configuration, we take both of them separately.

    For example:
        {"name": "MySinkConnector", "config": {"connector.class": "com.mongodb.kafka.connect.MongoSinkConnector", "connection.uri": "${MONGODB_URL}"}}
    """
    with open(configuration_file, "r", encoding="UTF-8") as file:
        config = json.load(file)
        asyncio.run(register_connector(ctx.obj.host, config))
