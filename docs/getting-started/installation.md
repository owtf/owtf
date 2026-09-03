# Install OWTF

Docker Compose is the supported way to run OWTF. Native installation is intended for contributors working on the codebase and is covered by the repository's [contributing guide](https://github.com/owtf/owtf/blob/develop/CONTRIBUTING.md).

## 1. Install the prerequisites

Install:

- [Git](https://git-scm.com/downloads)
- [Docker](https://docs.docker.com/get-docker/) with the Compose plugin

Confirm that both tools are available:

```bash
git --version
docker --version
docker compose version
```

## 2. Clone and start OWTF

```bash
git clone https://github.com/owtf/owtf.git
cd owtf
make compose-safe
```

The first build downloads base images and installs OWTF's dependencies, so it takes longer than later starts. The `compose-safe` target starts the split frontend, backend, and database development services without adding extra Linux capabilities to the application containers.

## 3. Open the web interface

Wait for the frontend and backend services to become ready, then open:

```text
http://localhost:8019
```

The backend API is on port `8009`; it is not the browser interface.

## Stop OWTF

Press ++ctrl+c++ in the Compose terminal. To stop a stack started in the background, run:

```bash
docker compose -f docker/docker-compose.dev.yml down
```

## Update a development checkout

Review local changes before pulling updates. From a clean checkout:

```bash
git switch develop
git pull --ff-only origin develop
make compose-safe
```

Compose rebuilds services whose inputs changed.
