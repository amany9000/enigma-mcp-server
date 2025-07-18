import contextlib
from collections.abc import AsyncIterator
import os, io
import click
import httpx
import uvicorn
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import PlainTextResponse
from starlette.types import Receive, Scope, Send

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from gramine_ratls.attest import write_ra_tls_key_and_crt

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    creds = None
    # token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        raise ValueError("token.json credential file not found")
    return build('drive', 'v3', credentials=creds)

def get_files(query, page_size=10):
    service = get_drive_service()
    results = service.files().list(
        q=f"name contains '{query}'",
        pageSize=page_size,
        fields="files(id, name, mimeType, modifiedTime)"
    ).execute()
    items = results.get('files', [])
    
    return items


def search_files(query, page_size=10):
    files = get_files(query, page_size)
    print('Files:')
    final_str = ''
    for file in files:
        final_str = final_str + f"{file['name']}, "
        print(f"{file['name']} (ID: {file['id']}, Type: {file['mimeType']})")
    return [types.TextContent(
        type="text",
        text=f"{len(files)} file(s) found: {final_str}"
    )]

def read_file(query, page_size=10):
    files = get_files(query, page_size)
    
    if len(files) == 0:
        return {'response': 'File not present'}

    if len(files) > 1:
        return {'response': 'More than one file present'}
    
    file_id = files[0]['id']
    file_name = files[0]['name']
    mime_type = files[0]['mimeType']
    
    service = get_drive_service()
    
    if mime_type == "application/vnd.google-apps.document":
        # Google Doc → export as plain text
        request = service.files().export_media(fileId=file_id, mimeType="text/plain")
    elif mime_type == "text/plain":
        # Plain text file
        request = service.files().get_media(fileId=file_id)
    else:
        print(f"Unsupported file type: {mime_type}")
        return

    # 📥 Download to buffer
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    buffer.seek(0)
    content = buffer.read().decode("utf-8")
    return [types.TextContent(
        type="text",
        text=f"--- Contents of {file_name} ---\n{content}\n"
    )]


@click.command()
@click.option("--port", default=8000, help="Port to listen on for StreamableHTTP")
@click.option(
    "--isDev",
    "isDev",
    is_flag=True,
    help="Is development mode on",
)
@click.option(
    "--auth",
    "auth",
    is_flag=True,
    help="Authenticate user for GDrive",
)
def main(port: int, isDev: bool, auth: bool) -> int:
    if auth:
        # Run local browser auth
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        return

    if not isDev:
        key_file_path = "/app/tmp/key.pem"
        crt_file_path = "/app/tmp/crt.pem"
        write_ra_tls_key_and_crt(key_file_path, crt_file_path, format="pem")

    app = Server("gdrive-mcp-server")

    @app.call_tool()
    async def gdrive_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if "fileName" not in arguments:
            raise ValueError("Missing required argument 'fileName'")
        if name == "search":
            return search_files(arguments["fileName"])
        elif name == "read":
            return read_file(arguments["fileName"])
        else:
            raise ValueError(f"Unknown tool: {name}")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="search",
                description="Searches for file with FileName in Google Drive",
                inputSchema={
                    "type": "object",
                    "required": ["fileName"],
                    "properties": {
                        "fileName": {
                            "type": "string",
                            "description": "FileName to search",
                        }
                    },
                },
            ),
            types.Tool(
                name="read",
                description="Read file with FileName in Google Drive",
                inputSchema={
                    "type": "object",
                    "required": ["fileName"],
                    "properties": {
                        "fileName": {
                            "type": "string",
                            "description": "FileName to read",
                        }
                    },
                },
            )
        ]

    # Create the session manager with true stateless mode
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=True,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            print("Application started with StreamableHTTP session manager!")
            try:
                yield
            finally:
                print("Application shutting down...")

    # Create an ASGI application using the transport
    starlette_app = Starlette(
        debug=True,
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )


    if isDev:
        uvicorn.run(starlette_app, host="0.0.0.0", port=port, workers=1, reload=False)
    else:
        uvicorn.run(starlette_app, host="0.0.0.0", port=port, workers=1, reload=False, ssl_keyfile=key_file_path, ssl_certfile=crt_file_path)

if __name__ == "__main__":
    main()