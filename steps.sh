docker image rm -f gsc-confidential-mcp-server gsc-confidential-mcp-server-unsigned confidential-mcp-server
docker build -t confidential-mcp-server .
cd docker/gsc
uv run ./gsc build -c ../confidential-mcp-server.config.yaml --rm confidential-mcp-server ../confidential-mcp-server.manifest
uv run ./gsc sign-image -c ../confidential-mcp-server.config.yaml  confidential-mcp-server "$HOME"/.config/gramine/enclave-key.pem
uv run ./gsc info-image gsc-confidential-mcp-server
cd ../../
docker run -p 8000:8000 --rm --env GRAMINE_MODE=direct \
    --security-opt seccomp=seccomp.json \
    gsc-confidential-mcp-server