# DevOps Console Backend

Provides DevOps Console Backend. This is an alpha version without APIs stability.

The main purpose is to provide a service (splitted in multiple services in the future) that will be able to communicate with all "DevOps" systems.
It will be the entrypoint for a DevOps Console UI but not restrictive to this only concern.

## Quick Start

Install
```bash
git clone --recurse-submodules https://github.com/croixbleueqc/devops-console-backend
cd devops-console-backend
python3.10 -m pip install ./_submodules/*
```


Run
```bash
BRANCH_NAME=dev python -m devops_console.run
```

or, with docker:

```bash
docker build -t devops-console-backend .
docker run -it --rm -e BRANCH_NAME=dev -p 5000:5000 devops-console-backend:local
```


## Swagger

```bash
curl http://localhost:5000/api/doc/swagger.json
```

You can use the Swagger UI at this location: http://localhost:5000/api/doc/

## WebSocket

More documentation are available under apis/wscom1.py and wscom.py
