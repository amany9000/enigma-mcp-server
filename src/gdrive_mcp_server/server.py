import contextlib, uvicorn
import os
import logging
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

# configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

from .config import config
from .tools import search_files, read_file, drive_manager


app = Server("gdrive-mcp-server")

_current_user = None

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


@app.call_tool()
async def gdrive_tool(name: str, arguments: dict) -> list:
    if config.OAUTH_STRICT and not _current_user:
        logger.warning("Unauthorized access attempt to gdrive_tool")
        raise ValueError("Unauthorized: Valid Google ID Token Required")

    filename = arguments.get("fileName")
    
    if name == "search":
        logger.debug("Searching for : %s", filename)
        return search_files(filename, _current_user) 

    elif name == "read":
        logger.debug("Reading file : %s", filename)
        return read_file(filename, _current_user)
    else:
        logger.error("Unknown tool call: %s", name)
        raise ValueError(f"Unknown tool: {name}")


session_manager = StreamableHTTPSessionManager(app=app, stateless=True)

async def handle_mcp_request(scope, receive, send):
    global _current_user

    headers = dict(scope.get("headers", []))
    auth_header = headers.get(b"authorization", b"").decode("utf-8")
    

    token = auth_header.replace("Bearer ", "") if "Bearer" in auth_header else None
    
    if not token:
        logger.warning("No token provided in request, returning 401")
        # on First Trigger, It will Return 401 with the metadata pointer
        # This will tells the client to look at your metadata endpoint
        response = JSONResponse(
            {"error": "Unauthorized"}, 
            status_code=401,
            headers={
                "WWW-Authenticate": f'Bearer resource_metadata="https://{config.DEPLOYED_HOST}/.well-known/oauth-protected-resource"'
            }
        )
        await response(scope, receive, send)
        return

    if config.OAUTH_STRICT:
        try:
            _current_user = drive_manager.verify_token(token)
            if not _current_user:
                logger.error("Token verification failed! Token might be expired or invalid.")
                raise ValueError("Unauthorized: Invalid or expired token")
        except Exception as e:
            logger.error("Error during token verification: %s", e)
            response = JSONResponse(
                {"error": "Unauthorized"}, 
                status_code=401,
                headers={
                    # "WWW-Authenticate": 'Bearer resource_metadata="https://hyperangelic-kathyrn-inflatedly.ngrok-free.dev/.well-known/oauth-protected-resource"'
                    "WWW-Authenticate": f'Bearer resource_metadata="https://{config.DEPLOYED_HOST}/.well-known/oauth-protected-resource"'
                }
            )
            await response(scope, receive, send)
            return

    # Call manager without the problematic kwarg
    await session_manager.handle_request(scope, receive, send)

async def handle_mcp_auth_challenge(scope, receive, send):
    headers = dict(scope.get("headers", []))
    auth = headers.get(b"authorization", b"").decode("utf-8")
    
    if not auth.startswith("Bearer "):
        # This generic 401 response triggers the 'Login' popup 
        # in VS Code, Claude, and Cursor automatically.
        response = JSONResponse(
            {"error": "unauthorized"},
            status_code=401,
            headers={
                "WWW-Authenticate": f'Bearer resource_metadata="https://{config.DEPLOYED_HOST}/.well-known/oauth-protected-resource"'
            }
        )
        await response(scope, receive, send)
        return

    # Valid token found? Hand off to the MCP logic
    await handle_mcp_request(scope, receive, send)

async def oauth_protected_resource(request):
    logger.debug("oauth_protected_resource called")
    return JSONResponse({
        "resource": f"https://{config.DEPLOYED_HOST}/mcp",
        "authorization_servers": ["https://accounts.google.com"],
        "scopes_supported": ["openid", "email", "https://www.googleapis.com/auth/drive.readonly", "profile"]
    })

async def oauth_authorization_server(request):
    logger.debug("oauth_authorization_server called, proxying Google's OIDC config")
    # You can simply proxy Google's standard OIDC config
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://accounts.google.com/.well-known/openid-configuration")
        return JSONResponse(resp.json())



@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    logger.info("Starting lifespan context with session manager")
    async with session_manager.run():
        yield
    logger.info("Ending lifespan context")

starlette_app = Starlette(
    routes=[
        Route("/.well-known/oauth-protected-resource", oauth_protected_resource),
        Route("/.well-known/oauth-authorization-server", oauth_authorization_server),
        Mount("/mcp", app=handle_mcp_request),
    ],
    lifespan=lifespan
)

if __name__ == "__main__":
    # Ensure key.pem and cert.pem are in your directory for HTTPS
    logger.info("Starting gdrive-mcp-server on %s:%d", config.HOST, config.PORT)
    uvicorn.run(
        starlette_app, 
        host=config.HOST, 
        port=config.PORT,
    )
    logger.info("gdrive-mcp-server has stopped")