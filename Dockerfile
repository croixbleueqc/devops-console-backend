FROM python:slim

ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1

# install poetry
RUN apt update && apt install -y curl \
    && curl -sSL https://install.python-poetry.org | python3 - --version 1.1.14

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /usr/src/app/

# Copy necessary files
COPY . .

# Install requirements while fetching upstream croixbleue dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --extras "local prod" --no-dev
# && poetry add "git+https://github.com/croixbleueqc/python-devops-sccs@f5b90008b1d0a21059e97fbcd7335760bc1f6325" \
# && poetry add "git+https://github.com/croixbleueqc/python-devops-kubernetes@27cc8d9e757b9d8daa473375977f24b736434cad" \

EXPOSE 5000
CMD gunicorn --bind 0.0.0.0:5000 --worker-class uvicorn.workers.UvicornWorker --access-logfile - --log-level info devops_console.main:app 
