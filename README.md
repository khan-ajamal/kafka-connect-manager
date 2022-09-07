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

-   `add`: Register new connector
-   `list`: List all connectors
-   `status`: Get status connector
-   `watch`: Actively monitor your connectors health

## `kcm add`

Register new connector

Supporting environment variable expansion in JSON file.

A connector requires a name and configuration, we take both of them separately.

For example:

```json
{
    "name": "MySinkConnector",
    "config": {
        "connector.class": "com.mongodb.kafka.connect.MongoSinkConnector",
        "connection.uri": "${MONGODB_URL}"
    }
}
```

**Usage**:

```console
$ kcm add [OPTIONS]
```

**Options**:

-   `-f, --file FILE`: Config JSON file path [required]
-   `--help`: Show this message and exit.

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

## `kcm watch`

Actively monitor your connectors health

![Dashboard Screenshot](https://res.cloudinary.com/ajamalkhan/image/upload/f_auto,q_auto/v1662560403/projects/kafka-connect-manager-watch-dashboard.png)

**Usage**:

```console
$ kcm watch [OPTIONS] [CONNECTORS]...
```

**Arguments**:

-   `[CONNECTORS]...`: Connectors to monitor

**Options**:

-   `--refresh-interval INTEGER`: Refresh interval [default: 5]
-   `--help`: Show this message and exit.
