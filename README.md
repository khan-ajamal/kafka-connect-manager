<h1 align="center">Kafka Connect Manager</h1>
<p align="center">A tool to manage Apache Kafka Connect connectors and tasks</p>

**Usage**:

```console
$ kcm [OPTIONS] COMMAND [ARGS]...
```

**Options**:

-   `--host TEXT`: Connect worker host [env var: CONNECT_HOST; default: http://localhost:8083]
-   `--install-completion`: Install completion for the current shell.
-   `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
-   `--help`: Show this message and exit.

**Commands**:

-   `list`: List all connectors
-   `status`: Get status connector

## `kcm list`

List all connectors

**Usage**:

```console
$ kcm list [OPTIONS]
```

**Options**:

-   `--type [all|sink|source]`: Type of connectors to list [default: all]
-   `--help`: Show this message and exit.

## `kcm status`

Get status connector

**Usage**:

```console
$ kcm status [OPTIONS]
```

**Options**:

-   `--connector TEXT`: Name of connector [required]
-   `--help`: Show this message and exit.
