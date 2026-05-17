# COMPOSE_SERVICE_AUDIT

Last updated: 2026-05-17

## Local Compose File

`docker-compose.yml` defines one service:

- `aggregator`
  - container name: `shi-aggregator`
  - volume: `./feed:/app/feed`
  - volume: `./logs:/app/logs`
  - environment: `FEED_DIR=/app/feed`, `LOGS_DIR=/app/logs`

No Executor service is defined in local compose.

## Local Docker Availability

`docker compose ps` could not run on the local Windows shell because `docker` is not available in PATH.

## Server Check

On `/opt/aitrader`, `shi-aggregator` was observed as `Up 10 days` on 2026-05-17. Server `feed/2026-05-17.csv` was actively appending non-synthetic rows with non-zero OHLC and volume.

## Verdict

Aggregator/feed health is alive on the server. Local Docker control is unavailable from this shell. Executor/live services were not run or changed.
