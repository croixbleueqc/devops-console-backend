# dev by default
ARG IS_LOCAL=true
FROM python:3.10-slim 

WORKDIR /usr/src/app

COPY . .

# see pyproject.toml to change prod revisions for local packages
RUN if [[ "$IS_LOCAL" = "false" ]]; then pip install --no-cache .[prod]; \
    else pip install --no-cache _submodules/* .; fi

EXPOSE 5000
