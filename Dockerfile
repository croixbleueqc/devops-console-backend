FROM python:3
EXPOSE 5000
EXPOSE 5001

WORKDIR /usr/src/app/

# Requirements not yet available on pypi

RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/devops-console-rest-api@2fb459ae352c9e81de565aa5b01646a0f7f4b87f
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-typing-engine@82e05fddff6d8eb264b28a523b0974a80c0e9d6c
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-aiobitbucket@a87c212408d8af4d07f6e02ccc0cc78931a27985
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-devops-sccs@07c8a71484a3c0eec68e25ce830ace535231301b
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-devops-kubernetes@f5b90008b1d0a21059e97fbcd7335760bc1f6325

# Copy necessary files
COPY devops_console devops_console
COPY setup.py .
COPY README.md .
COPY MANIFEST.in .

RUN pip install --no-cache-dir --compile .[prod]

# Remove source code to avoid any confusion with the real one executed.
RUN rm -rf ./devops_console setup.py README.md MANIFEST.in

CMD gunicorn devops_console.run:application --bind 0.0.0.0:5000 --worker-class aiohttp.worker.GunicornWebWorker --access-logfile - --log-level info
