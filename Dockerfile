FROM python:3.12-slim-bookworm

# Install the project into `/app`
WORKDIR /app

# Installing dependencies
COPY pyproject.toml token.json /app/
RUN pip install .

# Then copy src/
COPY src/ /app/src/
ENTRYPOINT []

CMD ["python", "-m", "src.gdrive_mcp_server", "--isDev"]
