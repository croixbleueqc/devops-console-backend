FROM python:3.10

# install poetry
RUN apt update && apt install -y curl
ENV POETRY_HOME=/opt/poetry
RUN POETRY_HOME=${POETRY_HOME} curl -sSL https://install.python-poetry.org | python3 - 
ENV PATH=$PATH:${POETRY_HOME}/bin

WORKDIR /usr/src/app/

# Copy necessary files
COPY devops_console ./devops_console
COPY pyproject.toml README.md MANIFEST.in ./
COPY _submodules ./_submodules

# Install requirements while fetching upstream croixbleue dependencies
RUN poetry install --extras "prod local" --no-dev
# RUN poetry add git+https://github.com/croixbleueqc/python-devops-sccs@f5b90008b1d0a21059e97fbcd7335760bc1f6325
# RUN poetry add git+https://github.com/croixbleueqc/python-devops-kubernetes@27cc8d9e757b9d8daa473375977f24b736434cad

# Remove source code to avoid any confusion with the real one executed.
RUN rm -rf devops_console pyproject.toml README.md MANIFEST.in _submodules

EXPOSE 5000
CMD gunicorn --bind 0.0.0.0:5000 --worker-class uvicorn.workers.UvicornWorker --access-logfile - --log-level info devops_console.main:app 
