FROM python:3
EXPOSE 5000
EXPOSE 5001

WORKDIR /usr/src/app/

# Requirements not yet available on pypi

RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/devops-console-rest-api@571218a21ec41b5871b4d639ec31eeb411373399
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-typing-engine@3f71bd9b30e688e28a00e3be5e2ff22a63058124
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-aiobitbucket@ebd1fda0cea4e2efa306cc65ca0797c17ca383c9
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-devops-sccs@7a429874fb154984314636218a3a7abf46420363
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-devops-kubernetes@c724ea4f11fd4838ce0040cd2db946634fb38379

# Copy necessary files
COPY devops_console devops_console
COPY setup.py .
COPY README.md .
COPY MANIFEST.in .

RUN pip install --no-cache-dir --compile .[prod]

# Remove source code to avoid any confusion with the real one executed.
RUN rm -rf ./devops_console setup.py README.md MANIFEST.in

CMD gunicorn devops_console.run:application --bind 0.0.0.0:5000 --worker-class aiohttp.GunicornWebWorker --access-logfile - --log-level info
