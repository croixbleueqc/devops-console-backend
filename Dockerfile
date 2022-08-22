# dev by default
ARG IS_LOCAL=true
FROM python:3.10-slim 

WORKDIR /app

COPY pyproject.toml ./
COPY _submodules ./_submodules

# see pyproject.toml to change prod revisions for local packages
RUN if [[ "$IS_LOCAL" = "false" ]]; then pip install --no-cache-dir -U .[prod]; else pip install --no-cache-dir -U _submodules/* .; fi

EXPOSE 5000
CMD ["uvicorn", "devops_console.main:app", "--host" "0.0.0.0", "--port", "5000"]
