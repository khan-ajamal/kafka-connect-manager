"""main.py contain application logic"""

import asyncio
from timeit import default_timer as timer

import httpx
from rich.table import Table
from rich.console import Console
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn

from kafka_connect_manager import constants
from kafka_connect_manager.utils import get_formatted_state


async def _get_active_connectors(host: str) -> list[str]:
    """Get list of active connectors"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{host}/connectors")
        return resp.json()


async def _get_connector_details(host: str, connector: str) -> dict:
    """Get connector configuration and tasks details"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{host}/connectors/{connector}")
        return resp.json()


async def _get_connector_status(host: str, connector: str) -> dict:
    """Get connector configuration and tasks details"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{host}/connectors/{connector}/status")
        return resp.json()


async def get_connectors(
    host: str,
    connector_type: constants.ConnectorType = constants.ConnectorType.ALL,
):
    """Get connectors based on its type"""
    start_ts = timer()

    connectors = []
    with Progress(SpinnerColumn(), transient=True) as progress:
        task1 = progress.add_task("Fetching connector", total=1)
        connectors = await _get_active_connectors(host)
        progress.update(task1, completed=1)
    rprint(
        f"\n[bold green]Total Connectors Found: [/bold green]{len(connectors)} :boom:\n"
    )

    tasks = [_get_connector_details(host, connector) for connector in connectors]

    connector_details = []
    with Progress(transient=True) as progress:
        pg_task = progress.add_task("Fetching connector details", total=len(tasks))
        for detail_task in asyncio.as_completed(tasks):
            connector_detail = await detail_task
            progress.advance(task_id=pg_task, advance=1)

            if (
                connector_type != constants.ConnectorType.ALL
                and connector_type != connector_detail["type"]
            ):
                # skip if connector type does not match
                continue

            connector_details.append(
                {
                    "name": connector_detail["name"],
                    "class": connector_detail["config"]["connector.class"].split(".")[
                        -1
                    ],
                    "type": connector_detail["type"],
                    "tasks": len(connector_detail["tasks"]),
                }
            )

    table = Table(
        title=f"{str(connector_type.value).capitalize()} connectors",
        caption=(
            f"{len(connector_details)} {str(connector_type.value).capitalize()} connectors found"
        ),
    )
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Connector Class")
    table.add_column("Tasks Count", justify="center")

    for connector_detail in connector_details:
        table.add_row(
            connector_detail["name"],
            connector_detail["type"],
            connector_detail["class"],
            str(connector_detail["tasks"]),
        )

    console = Console()
    console.print(table)
    end_ts = timer()

    rprint(f"\n[bold green]Elapsed time: [/bold green]{round(end_ts - start_ts, 4)}")


async def get_connector_status(host: str, connector_name: str):
    """Get status of connector along with status of tasks"""
    status = await _get_connector_status(host, connector_name)

    rprint(f"\n[bold]Name - [/bold]{status['name']}")
    rprint(f"[bold]State - [/bold]{get_formatted_state(status['connector']['state'])}")
    rprint(f"[bold]Worker ID - [/bold]{status['connector']['worker_id']}")
    rprint("\n")
    connector_task_status_table = Table(title="[bold blue]Tasks Status")
    connector_task_status_table.add_column("ID")
    connector_task_status_table.add_column("State", justify="left")
    connector_task_status_table.add_column("Worker ID")

    for task_detail in status["tasks"]:
        connector_task_status_table.add_row(
            str(task_detail["id"]),
            get_formatted_state(task_detail["state"]),
            task_detail["worker_id"],
        )

    console = Console()
    console.print(connector_task_status_table)
