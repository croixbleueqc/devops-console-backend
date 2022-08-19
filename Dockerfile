ARG IS_LOCAL=false
FROM python:3.10-slim 

COPY dist/*.whl /tmp/

RUN if [[ "$IS_LOCAL" = "false" ]]; then \
    pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-devops-kubernetes.git@27cc8d9e757b9d8daa473375977f24b736434cad \
    git+https://github.com/croixbleueqc/python-devops-sccs.git@f5b90008b1d0a21059e97fbcd7335760bc1f6325; \
    rm /tmp/*sccs*.whl /tmp/*kubernetes*.whl; \
    fi
RUN pip install /tmp/*.whl

EXPOSE 5000
CMD ["gunicorn" "--bind" "0.0.0.0:5000" "--worker-class" "uvicorn.workers.UvicornWorker" "--access-logfile" "-" "--log-level" "info" "devops_console.main:app" ]
