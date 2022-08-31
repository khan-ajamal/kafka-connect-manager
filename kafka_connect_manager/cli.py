"""cli.py contains cli commands"""
from types import SimpleNamespace

import typer

from kafka_connect_manager import constants

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
    print(ctx.obj.host)
    print(connector_type)
