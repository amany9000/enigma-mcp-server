FROM python:3.11-bullsey

# Install the project into `/app`
WORKDIR /app

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app
RUN pip install -r requirements.txt 

# Place executables in the environment at the front of the path

ENTRYPOINT []

CMD ["python", "/app/src/attestable_mcp_server/__main__.py"]
