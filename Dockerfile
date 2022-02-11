FROM python:3
EXPOSE 5000
EXPOSE 5001

WORKDIR /usr/src/app/

# Requirements not yet available on pypi
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-typing-engine@3f71bd9b30e688e28a00e3be5e2ff22a63058124
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-aiobitbucket@ebd1fda0cea4e2efa306cc65ca0797c17ca383c9
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-devops-sccs@7510622e8abd8a631385a0ffd484b2edc9c4a98f
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-devops-kubernetes@c724ea4f11fd4838ce0040cd2db946634fb38379

# Copy necessary files
COPY devops_console devops_console
COPY setup.py .
COPY README.rst .
COPY MANIFEST.in .

RUN pip install --no-cache-dir --compile .[prod]

# Remove source code to avoid any confusion with the real one executed.
RUN rm -rf ./devops_console setup.py README.rst MANIFEST.in

CMD gunicorn devops_console.run:application --bind 0.0.0.0:5000 --worker-class aiohttp.GunicornWebWorker --access-logfile - --log-level info
