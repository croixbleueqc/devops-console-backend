FROM python:3.10

# install poetry
RUN apt update && apt install -y curl
ENV POETRY_HOME /opt/poetry
RUN curl -sSL https://install.python-poetry.org | python3 - 
ENV PATH $PATH:${POETRY_HOME}/bin/poetry

WORKDIR /usr/src/app/

# Copy necessary files
COPY devops_console devops_console
COPY pyproject.toml README.md MANIFEST.in ./

# Install requirements while fetching upstream croixbleue dependencies
RUN poetry install --extras prod --no-dev
RUN poetry add git+https://github.com/croixbleueqc/python-devops-sccs@07c8a71484a3c0eec68e25ce830ace535231301b
RUN poetry add git+https://github.com/croixbleueqc/python-devops-kubernetes@f5b90008b1d0a21059e97fbcd7335760bc1f6325

# Remove source code to avoid any confusion with the real one executed.
RUN rm -rf devops_console pyproject.toml poetry.lock README.md MANIFEST.in _submodules

EXPOSE 5000
CMD gunicorn --bind 0.0.0.0:5000 --worker-class uvicorn.workers.UvicornWorker --access-logfile - --log-level info devops_console.main:app 
