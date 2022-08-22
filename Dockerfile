# dev by default
ARG IS_LOCAL=true
FROM python:3.10-slim 

WORKDIR /usr/src/app

COPY . .

# see pyproject.toml to change prod revisions for local packages
RUN if [[ "$IS_LOCAL" = "false" ]]; then pip install .[prod]; \
    else pip install _submodules/* .; fi

RUN rm -rf devops_console

EXPOSE 5000
# CMD ["uvicorn", "devops_console.main:app", "--host" "0.0.0.0", "--port", "5000"]
