# ➡️ confidential-mcp-server
<div align="center">

<strong>Confidential MCP server</strong>
</div>

## Overview

A Confidential MCP Server implementation running on [Gramine](https://github.com/gramineproject/gramine). It connects to your Google drive to Read/Search File.
  
## Dependencies
 - Intel SGX Hardware
 - Gramine
 - python 3.13
 - Ubuntu 22.04
 - Intel SGX SDK & PSW

## Getting started with Gdrive

1. [Create a new Google Cloud project](https://console.cloud.google.com/projectcreate)
2. [Enable the Google Drive API](https://console.cloud.google.com/workspace-api/products)
3. [Configure an OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent) ("internal" is fine for testing)
4. Add OAuth scope `https://www.googleapis.com/auth/drive.readonly`
5. [Create an OAuth Client ID](https://console.cloud.google.com/apis/credentials/oauthclient) for application type "Desktop App"
6. Download the JSON file of your client's OAuth keys
7. Rename the key file to `credentials.json` and place into the root of this repo.

## Initial Setup
Setup Venv:
```
python -m venv .venv
source .venv/bin/activate
```
Install Deps:
```
pip install -r requirements.txt
```

## Authentication
To authenticate and save credentials:

1. Run: `python -m src.gdrive_mcp_server --isDev --auth `
2. This will open an authentication flow in your system browser
3. Complete the authentication process
4. Credentials will be saved in the root of this repo (i.e. `./token.json`)

## Local Development
```
python -m src.gdrive_mcp_server --isDev 
```

## Production

```
docker build -t confidential-mcp-server .
gramine-sgx-gen-private-key
git clone https://github.com/gramineproject/gsc docker/gsc
cd docker/gsc
./gsc build-gramine --rm --no-cache -c ../gramine_base.config.yaml gramine_base
./gsc build -c ../confidential-mcp-server.config.yaml --rm confidential-mcp-server ../confidential-mcp-server.manifest
./gsc sign-image -c ../confidential-mcp-server.config.yaml  confidential-mcp-server "$HOME"/.config/gramine/enclave-key.pem
./gsc info-image gsc-confidential-mcp-server
```

Note: Build gramine_base only once.

## Starting Server in Direct Mode
```
docker run -it --rm \
  --security-opt seccomp=unconfined \
  --cap-add=SYS_PTRACE \
  --cap-add=SYS_ADMIN \
  -e GRAMINE_MODE=direct \
  gsc-confidential-mcp-server
```


## Starting Server on Secure Hardware
```
docker run -itp --device=/dev/sgx_provision:/dev/sgx/provision  --device=/dev/sgx_enclave:/dev/sgx/enclave -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket -p 8000:8000 --rm gsc-confidential-mcp-server
```
