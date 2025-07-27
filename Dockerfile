FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install the project into `/app`
WORKDIR /app

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app
RUN pip install .

# Place executables in the environment at the front of the path

ENTRYPOINT []

CMD ["python", "-m", "src.gdrive_mcp_server", "--isDev"]
