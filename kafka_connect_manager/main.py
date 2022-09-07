"""main.py contain application logic"""
import asyncio
from datetime import datetime
from collections import defaultdict
from timeit import default_timer as timer

import typer
import httpx

from rich.text import Text
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.console import Console
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn

from kafka_connect_manager import constants
from kafka_connect_manager.utils import (
    expand_environment_variables,
    get_formatted_state,
    slugify,
)


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


async def _register_connector(host: str, config: dict) -> dict:
    """Get connector configuration and tasks details"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{host}/connectors", json=config)
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


def validate_connector_configuration(config: dict):
    """Validate configuration that all required fields are provided"""
    required_fields = ["connector.class"]

    missing_fields = []
    for field in required_fields:
        if field not in config.keys():
            missing_fields.append(field)

    if missing_fields:
        raise typer.BadParameter(
            f"Following fields are missing: {','.join(missing_fields)}"
        )


async def register_connector(host: str, connector_config: dict):
    """Register connector"""
    # expand environment variables
    expand_environment_variables(connector_config)

    if not connector_config.get("name") or not connector_config.get("config"):
        raise typer.BadParameter(
            "`name` and `config` are required field for configuration JSON"
        )

    connector_name = slugify(str(connector_config.get("name")))
    if connector_config.get("config"):
        connector_config = connector_config.get("config") or {}

    # validate config to have basic information available
    validate_connector_configuration(connector_config)

    config = {"name": connector_name, "config": connector_config}
    resp = await _register_connector(host, config)
    if resp.get("error_code"):
        raise typer.BadParameter(resp["message"])

    rprint(f"\n[bold green]Connector Registered: [/bold green]{connector_name}")


async def _get_monitoring_dashboard(host: str, connectors: list[str]) -> Table:
    """Monitoring dashboard"""
    tasks = [_get_connector_status(host, connector) for connector in connectors]

    invalid_connectors = []
    connector_metrics: dict = defaultdict(int)
    task_metrics: dict = defaultdict(int)
    workers = set()
    for detail_task in asyncio.as_completed(tasks):
        connector_detail = await detail_task
        if connector_detail.get("error_code"):
            invalid_connectors.append(connector_detail["message"])
            continue

        connector_metrics["total"] += 1
        workers.add(connector_detail["connector"]["worker_id"])

        if connector_detail["connector"]["state"] == constants.ConnectorState.RUNNING:
            connector_metrics["active"] += 1
        else:
            connector_metrics["failed"] += 1

        task_metrics["total"] += len(connector_detail["tasks"])

        for task in connector_detail["tasks"]:
            if task["state"] == constants.ConnectorState.RUNNING:
                task_metrics["active"] += 1
            else:
                task_metrics["failed"] += 1
    total_connector_panel = Panel.fit(
        Text(str(connector_metrics["total"]), justify="center", style="bold gray"),
        title="Total Connectors",
        padding=(2, 2),
    )
    active_connector_panel = Panel.fit(
        Text(str(connector_metrics["active"]), justify="center", style="bold green"),
        title="Active Connectors",
        padding=(2, 2),
    )
    failed_connector_panel = Panel.fit(
        Text(str(connector_metrics["failed"]), justify="center", style="bold red"),
        title="Failed Connectors",
        padding=(2, 2),
    )

    # Task panels
    total_tasks_panel = Panel.fit(
        Text(str(task_metrics["total"]), justify="center", style="bold gray"),
        title="Total Tasks",
        padding=(2, 2),
    )
    active_tasks_panel = Panel.fit(
        Text(str(task_metrics["active"]), justify="center", style="bold green"),
        title="Active Tasks",
        padding=(2, 2),
    )
    failed_tasks_panel = Panel.fit(
        Text(str(task_metrics["failed"]), justify="center", style="bold red"),
        title="Failed Tasks",
        padding=(2, 2),
    )

    # workers
    workers_panel = Panel.fit(
        Text(str(len(workers)), justify="center", style="bold blue"),
        title="Workers Count",
        padding=(2, 2),
    )
    grid = Table.grid(expand=True)
    grid.add_column()

    now = datetime.now().strftime("%H:%M:%S")
    grid.add_row(
        Text(
            f"Last updated at: {now}",
            justify="right",
            end="",
        )
    )
    grid.add_row(
        Columns(
            [
                workers_panel,
                total_connector_panel,
                active_connector_panel,
                failed_connector_panel,
                total_tasks_panel,
                active_tasks_panel,
                failed_tasks_panel,
            ]
        )
    )

    return grid


async def monitor_connectors(
    host: str, connectors: list[str] | None = None, refresh_interval: int = 5
):
    """Monitor connectors state along with its tasks

    Args:
        host: endpoint of worker node
        connectors: List of connectors to monitor
        refresh_interval: Number of seconds data will be refreshed
    """
    if not connectors:
        connectors = await _get_active_connectors(host)

    dashboard = await _get_monitoring_dashboard(host, connectors)
    with Live(dashboard, refresh_per_second=refresh_interval) as live:
        while True:
            await asyncio.sleep(refresh_interval)
            dashboard = await _get_monitoring_dashboard(host, connectors)
            live.update(dashboard)
