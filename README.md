# ➡️ Enigma-mcp-server
<div align="center">

<strong>Enigma MCP server</strong>
</div>

## Overview

A confidential MCP Server implementation running on [Gramine](https://github.com/gramineproject/gramine). It connects to your Google drive to Read/Search File.
  
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
pip install .[dev]
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
First clone gsc:
```
git clone https://github.com/gramineproject/gsc docker/gsc
```
Then generate enclave private key:
```
gramine-sgx-gen-private-key
```
Build gramine base (just once):
```
./gsc build-gramine --rm --no-cache -c ../gramine_base.config.yaml gramine_base
```

### Image building, graminisation and signing
```
docker build -t enigma-mcp-server .
cd docker/gsc
./gsc build -c ../enigma-mcp-server.config.yaml --rm enigma-mcp-server ../enigma-mcp-server.manifest
./gsc sign-image -c ../enigma-mcp-server.config.yaml  enigma-mcp-server "$HOME"/.config/gramine/enclave-key.pem
./gsc info-image gsc-enigma-mcp-server
```

### Starting Server in Direct Mode
```
docker run -p 8000:8000 --rm --env GRAMINE_MODE=direct \
  --security-opt seccomp=seccomp.json \
  gsc-enigma-mcp-server
```

The repetetive steps from above after building gramine_base and present in steps.sh and can be executed using:
```
bash steps.sh
```

## Starting Server on Secure Hardware
```
docker run -itp --device=/dev/sgx_provision:/dev/sgx/provision  --device=/dev/sgx_enclave:/dev/sgx/enclave -v /var/run/aesmd/aesm.socket:/var/run/aesmd/aesm.socket -p 8000:8000 --rm gsc-enigma-mcp-server
```
