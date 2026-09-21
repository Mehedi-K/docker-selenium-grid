# docker-selenium-grid

![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Selenium Grid](https://img.shields.io/badge/Selenium%20Grid-4.25-43B02A?logo=selenium&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![pytest](https://img.shields.io/badge/Tests-pytest-0A9EDC?logo=pytest&logoColor=white)
![CI](https://github.com/Mehedi-K/docker-selenium-grid/actions/workflows/ci.yml/badge.svg)

A containerized **Selenium Grid** — one hub plus Chrome and Firefox nodes —
defined entirely in Docker Compose, with a small pytest smoke-test suite
that proves the grid actually works by running real `RemoteWebDriver`
sessions against it. GitHub Actions stands the whole stack up, runs the
tests, and tears it down on every push and pull request.

This is a portfolio project focused on **test infrastructure** rather than
test authoring: standing up disposable, reproducible browser infrastructure
with Docker so that test suites (in any language) don't need browsers or
drivers installed on the machine that runs them.

## Why a Selenium Grid?

A Selenium Grid decouples *where tests run* from *what browsers they run
against*. A hub accepts WebDriver sessions and routes them to registered
browser nodes, which means:

- **Cross-browser coverage** — the same test suite can target Chrome or
  Firefox by changing one capability, without installing either browser
  locally.
- **Parallel execution** — multiple nodes (or multiple replicas of a node)
  let sessions run concurrently instead of queueing behind a single local
  browser.
- **Environment isolation** — browser versions and drivers live inside the
  node containers, not on the host or the CI runner, so "works on my
  machine" stops being a browser-version problem.
- **A stable target for other repos** — any Selenium-based suite (Java,
  Python, JS/TS) can point at this grid over the network via a single
  `SELENIUM_REMOTE_URL`/hub endpoint instead of managing local drivers.

## Architecture

```
                 ┌────────────────────┐
   RemoteWebDriver│   selenium-hub     │  :4444  Grid console / WebDriver API
   clients ──────▶│  (routes sessions) │  :4442  event bus (publish)
                 └─────────┬──────────┘  :4443  event bus (subscribe)
                           │
            selenium-grid (bridge network)
                           │
          ┌────────────────┴────────────────┐
          ▼                                  ▼
   ┌─────────────┐                   ┌──────────────┐
   │ chrome node │                   │ firefox node │
   └─────────────┘                   └──────────────┘
```

The hub and nodes register with each other over a dedicated `selenium-grid`
bridge network using their Compose service names (`selenium-hub`, `chrome`,
`firefox`) — nothing is wired to a host IP or local hostname, so the same
`docker-compose.yml` runs unmodified on any machine or CI runner.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (Desktop or Engine)
- Docker Compose v2 (bundled with modern Docker Desktop/Engine as
  `docker compose`)
- Python 3.9+ if you want to run the smoke tests from your host instead of
  relying on CI

## Starting the grid

```bash
docker compose up -d
```

This pulls (if needed) and starts `selenium-hub`, one `chrome` node, and one
`firefox` node, all on the `selenium-grid` network. The hub exposes:

- **`http://localhost:4444`** — live Grid console (see registered nodes,
  active sessions, session queue)
- **`http://localhost:4444/wd/hub`** — the WebDriver endpoint tests connect
  to
- **`http://localhost:4444/wd/hub/status`** — machine-readable readiness
  check, used by CI to know when the grid is up

Want more capacity for one browser? Scale nodes with Compose instead of
editing the file:

```bash
docker compose up -d --scale chrome=2
```

## Running the smoke tests

The smoke-test suite in `smoke-tests/` is a standalone pytest project. It
opens real `RemoteWebDriver` sessions against the grid and drives them
through [the-internet.herokuapp.com](https://the-internet.herokuapp.com/), a
public site built for exercising exactly this kind of browser automation.

```bash
cd smoke-tests
pip install -r requirements.txt

# with the grid already running (docker compose up -d):
SELENIUM_REMOTE_URL=http://localhost:4444/wd/hub pytest -v

# target Firefox instead of the default Chrome:
SELENIUM_REMOTE_URL=http://localhost:4444/wd/hub BROWSER=firefox pytest -v
```

On any test failure, a screenshot is saved to `smoke-tests/screenshots/`
(gitignored locally, uploaded as a CI artifact on failure).

## Pointing an external test suite at this grid

Any of this account's other Selenium-based repos (`selenium-java`,
`robot-framework-python`) can run against this grid instead of a local
browser by starting the grid here and pointing the other project's remote
URL / hub environment variable at it, e.g.:

```bash
# in this repo
docker compose up -d

# in another repo's test run
SELENIUM_REMOTE_URL=http://localhost:4444/wd/hub mvn test -Dremote=true
```

The exact variable name depends on that project's driver factory, but the
target is always the same: `http://localhost:4444/wd/hub`.

## Tearing down

```bash
docker compose down
```

Add `-v` to also remove the network's anonymous volumes if you scaled nodes
during the session.

## Continuous Integration

`.github/workflows/ci.yml` runs on every push and pull request to `main`:

1. Starts the full stack with `docker compose up -d`.
2. Polls `http://localhost:4444/wd/hub/status` until the hub reports ready
   (with a bounded retry loop, not a fixed sleep).
3. Installs the smoke-test dependencies and runs the suite against the grid
   — once for Chrome and once for Firefox, as a matrix.
4. Uploads screenshots and JUnit XML as build artifacts if anything fails.
5. Always tears the stack down with `docker compose down -v`, even if the
   tests failed.

## Project structure

```
docker-selenium-grid/
  docker-compose.yml          Hub + Chrome node + Firefox node on a shared bridge network
  smoke-tests/
    requirements.txt          selenium, pytest
    conftest.py                RemoteWebDriver fixture (SELENIUM_REMOTE_URL, BROWSER), failure screenshots
    test_grid_smoke.py        6 end-to-end tests proving the grid routes real sessions
  .github/workflows/ci.yml    Stands the grid up, runs the smoke tests, tears it down
  .gitignore
```
