# DevOps Console Backend

Provides DevOps Console Backend. This is an alpha version without APIs stability.

The main purpose is to provide a service (split in multiple services in the future) that will be able to communicate with all "DevOps" systems.

It will be the entrypoint for a DevOps Console UI but not restrictive to this only concern.

## Quick Start

### Install

```bash
python -m venv .venv # Create a python virtual environment
source .venv/bin/activate # Activate it 
python -m pip install -e . # Install local package
```

### Run

```bash
BRANCH_NAME=dev python -m devops_console.main
```

### or, with docker:

```bash
docker build -t devops-console-backend:local .
docker run -it -p 5000:5000 devops-console-backend:local
```

## Endpoints

[http://localhost:5000/docs](http://localhost:5000/docs): OpenApi spec
[http://localhost:5000](http://localhast:5000): Server address
