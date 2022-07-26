FROM python:3
EXPOSE 5000
EXPOSE 5001

WORKDIR /usr/src/app/

# Requirements not yet available on pypi

RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/devops-console-rest-api@80d1e91605e8514944836c608dc7fdbd035a5169
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-typing-engine@22b40af671f029af6a47ac8387e4ce5125d36181
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-aiobitbucket@38e45bed6fce9aba8bba12650188d4f110be8c35
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-devops-sccs@316075f137279be9a580e62123594c98817a36b8
RUN pip install --no-cache-dir --compile git+https://github.com/croixbleueqc/python-devops-kubernetes@bd720d23aee67d73272ea1e33cb2a5cd743cfcef

# Copy necessary files
COPY devops_console devops_console
COPY setup.py .
COPY README.md .
COPY MANIFEST.in .

RUN pip install --no-cache-dir --compile .[prod]

# Remove source code to avoid any confusion with the real one executed.
RUN rm -rf ./devops_console setup.py README.md MANIFEST.in

CMD gunicorn devops_console.run:application --bind 0.0.0.0:5000 --worker-class aiohttp.worker.GunicornWebWorker --access-logfile - --log-level info
